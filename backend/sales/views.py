from django.db import transaction
from django.db.models import F, ExpressionWrapper, DecimalField, Sum, Value
from rest_framework import viewsets
from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import QuotationDetail, QProductDetail
from .models import BillDetail, ProductDetail
from clients.models import Client

from .serializers import (
    QuotationDetailSerializer,
    QProductDetailSerializer,
)
from sales.serializers import BillDetailSerializer, ProductDetailSerializer
from sales.filters import BillFilter, QuotationFilter
from utils.pdf_generator import generate_pdf


class BaseDashboardMixin:
    """Common dashboard methods for bills and quotations."""

    def aggregate_totals(self, queryset, price_expr, gst_expr):
        """Aggregate totals from database directly."""
        totals = queryset.aggregate(
            total_amount=Sum(price_expr + gst_expr),
            total_gst=Sum(gst_expr),
            total_units=Sum(F("product_quantity")),
        )
        return totals


class QuotationViewSet(BaseDashboardMixin, viewsets.ModelViewSet):
    serializer_class = QuotationDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = QuotationFilter
    ordering_fields = ["date", "total_amount_after_gst", "quotationno"]
    ordering = ["-date"]

    def get_queryset(self):
        return QuotationDetail.objects.filter(
            party__user=self.request.user
        ).prefetch_related("quotationdetails")

    def perform_create(self, serializer):
        with transaction.atomic():
            quotation = serializer.save()
            quotation.update_totals()
            return quotation

    def perform_update(self, serializer):
        with transaction.atomic():
            quotation = serializer.save()
            quotation.update_totals()
            return quotation

    @action(detail=False, methods=["post"], url_name="pdf")
    def pdf(self, request):
        pdf_path = generate_pdf(request.data, "quotation.pdf", doc_type="quotation")
        return Response({"msg": f"Your quotation PDF is saved at {pdf_path}"})

    @action(detail=False, methods=["get"], url_name="dashboard")
    def dashboard(self, request):
        party_name = request.query_params.get("party_name")

        if not party_name:
            return Response({"error": "party_name required"}, status=400)

        query = {"quotationno__party__user": self.request.user}
        if party_name:
            query["quotationno__party__name"] = party_name

        products = (
            QProductDetail.objects.filter(**query)  # unpack the dict
            .select_related("quotationno")
            .annotate(
                price=F("unit_price") * F("product_quantity"),
                gst_rate=F("igst") + F("sgst") + F("cgst"),
                product_gst=ExpressionWrapper(
                    F("unit_price")
                    * F("product_quantity")
                    * (F("igst") + F("sgst") + F("cgst"))
                    / 100,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                total=ExpressionWrapper(
                    F("unit_price")
                    * F("product_quantity")
                    * (1 + (F("igst") + F("sgst") + F("cgst")) / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
        )

        totals = self.aggregate_totals(products, F("price"), F("product_gst"))
        bill_count = products.values("quotationno_id").distinct().count()

        return Response(
            {
                "party_name": party_name,
                "total_amount": totals["total_amount"] or 0,
                "total_gst": totals["total_gst"] or 0,
                "total_units": totals["total_units"] or 0,
                "total_quotations": bill_count,
            }
        )


class BillDetailViewSet(BaseDashboardMixin, viewsets.ModelViewSet):
    serializer_class = BillDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BillFilter
    ordering_fields = ["date", "total_amount_after_gst", "billno"]
    ordering = ["-date"]

    def get_queryset(self):
        return BillDetail.objects.filter(
            party__user=self.request.user
        ).prefetch_related("productdetails")

    def perform_create(self, serializer):
        with transaction.atomic():
            bill = serializer.save()
            bill.update_totals()
            return bill

    def perform_update(self, serializer):
        with transaction.atomic():
            bill = serializer.save()
            bill.update_totals()
            return bill

    @action(detail=True, methods=["get"], url_name="dashboard")
    def dashboard(self, request, pk=None):
        party_name = request.query_params.get("party_name")
        if not party_name:
            return Response({"error": "party_name required"}, status=400)

        products = (
            ProductDetail.objects.filter(
                billno__party__user=self.request.user, billno__party__name=party_name
            )
            .select_related("billno")
            .annotate(
                price=F("unit_price") * F("product_quantity"),
                gst_rate=F("igst") + F("sgst") + F("cgst"),
                product_gst=ExpressionWrapper(
                    F("unit_price")
                    * F("product_quantity")
                    * (F("igst") + F("sgst") + F("cgst"))
                    / 100,
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
                total=ExpressionWrapper(
                    F("unit_price")
                    * F("product_quantity")
                    * (1 + (F("igst") + F("sgst") + F("cgst")) / 100),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
        )

        totals = self.aggregate_totals(products, F("price"), F("product_gst"))
        bill_numbers = products.values_list("billno__billno", flat=True).distinct()

        return Response(
            {
                "party_name": party_name,
                "total_amount": totals["total_amount"] or 0,
                "total_gst": totals["total_gst"] or 0,
                "total_units": totals["total_units"] or 0,
                "total_bills": bill_numbers.count(),
            }
        )

    @action(detail=False, methods=["post"], url_name="pdf")
    def pdf(self, request):
        pdf_path = generate_pdf(request.data, "invoice.pdf", doc_type="invoice")
        return Response({"msg": f"Your invoice PDF is saved at {pdf_path}"})

    @action(
        detail=False,
        methods=["post"],
        url_path="create-from-quotation",
        url_name="create-from-quotation",
    )
    def create_from_quotation(self, request):
        """
        Create a Bill (Invoice) by copying an existing Quotation.
        Expects: { "quotation_id": <id> }
        """
        quotation_id = request.data.get("quotation_id")
        if not quotation_id:
            return Response({"error": "quotation_id is required"}, status=400)

        quotation = get_object_or_404(QuotationDetail, id=quotation_id)

        with transaction.atomic():
            # Create bill from quotation
            bill_data = {
                "party": quotation.party,
                "date": quotation.date,
                "transportmode": request.data.get("transportmode", ""),
                "vehicleno": request.data.get("vehicleno", ""),
                "dateofsupply": request.data.get("dateofsupply", quotation.date),
                "placeofsupply": request.data.get("placeofsupply", ""),
                "gstrc": request.data.get("gstrc", ""),
                "tc": quotation.tc,
                "is_paid": False,
            }
            bill = BillDetail.objects.create(**bill_data)

            # Copy products
            for qprd in quotation.quotationdetails.all():
                ProductDetail.objects.create(
                    billno=bill,
                    hsncode=qprd.hsncode,
                    cgst=qprd.cgst,
                    sgst=qprd.sgst,
                    igst=qprd.igst,
                    product_discription=qprd.product_discription,
                    product_quantity=qprd.product_quantity,
                    unit_type=qprd.unit_type,
                    unit_price=qprd.unit_price,
                )

            bill.refresh_from_db()
            bill.update_totals()

        serializer = self.get_serializer(bill)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
