from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from utils.common import get_current_financial_date, MONTHS
from sales.models import QuotationDetail, BillDetail
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Case, When, F, FloatField
from django.db.models.functions import ExtractMonth
from django.db.models import Count
from datetime import date, datetime
from clients.models import Client

from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date


import calendar
import pdfkit
from django.template import loader
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .utils import bill_annotations


# Download invoice & quotation month wise
class DownloadReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        month = int(request.data.get("month"))
        year = int(request.data.get("year"))
        user = request.user

        # --- Filters ---
        bill_filters = {"date__month": month, "date__year": year, "party__user": user}

        # --- Aggregated report ---
        report = BillDetail.objects.filter(**bill_filters).aggregate(
            **bill_annotations()
        )
        total_bills = BillDetail.objects.filter(**bill_filters).count()

        # --- Purchase bills ---
        purchase_filters = {
            "bill_date__month": month,
            "bill_date__year": year,
            "user": user,
        }
        purchase_bills = BillDetail.objects.filter(**purchase_filters).aggregate(
            total_gst=Sum("bill_gst"),
            total_bills_amount=Sum("bill_amount"),
            total_bills=Count("id"),
        )

        # --- Bills with annotation per bill ---
        bills = BillDetail.objects.filter(**bill_filters).annotate(**bill_annotations())

        # --- GST difference ---
        t_total_cgst = float(report.get("total_cgst") or 0)
        t_total_igst = float(report.get("total_igst") or 0)
        t_total_sgst = float(report.get("total_sgst") or 0)
        p_total_gst = float(purchase_bills.get("total_gst") or 0)
        gst_to_be_paid = (t_total_cgst + t_total_igst + t_total_sgst) - p_total_gst

        # --- Context ---
        context = {
            "reports": report,
            "month": calendar.month_name[month],
            "year": year,
            "total_bills": total_bills,
            "bills": bills,
            "user": user,
            "purchase_bills": purchase_bills,
            "gst_to_be_paid": gst_to_be_paid,
        }

        # --- Render to PDF ---
        html = loader.render_to_string("general/report_pdf.html", context)
        output = pdfkit.from_string(html, output_path=False)
        response = HttpResponse(content_type="application/pdf")
        response.write(output)
        return response


class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Dashboard summary API
        Query Params:
            from_date (YYYY-MM-DD) - optional
            to_date   (YYYY-MM-DD) - optional
            is_paid   (true/false) - optional
        """
        user = request.user
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        is_paid = request.query_params.get("is_paid", "false").lower() == "true"

        # --- Filters ---
        bill_filters = {"party__user": user, "is_paid": is_paid}
        quotation_filters = {"party__user": user}

        if from_date and to_date:
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
                bill_filters["date__range"] = (from_date, to_date)
                quotation_filters["date__range"] = (from_date, to_date)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."}, status=400
                )

        # --- Bill Calculations ---
        bill_qs = BillDetail.objects.filter(**bill_filters)
        bill_calculation = bill_qs.aggregate(
            total_amount_with_gst=Sum("total_amount_after_gst"),
            total_gst=Sum("total_gst_amount"),
        )
        bill_count = bill_qs.count()

        # --- Quotation Calculations ---
        quotation_qs = QuotationDetail.objects.filter(**quotation_filters)
        quotation_calculations = quotation_qs.aggregate(
            q_total_amount_with_gst=Sum("total_amount_after_gst"),
            q_total_gst=Sum("total_gst_amount"),
        )
        quotation_count = quotation_qs.count()

        # --- Party Count ---
        party_count = Client.objects.filter(user=user).count()

        # --- Safe Calculations (avoid None) ---
        total_amount_with_gst = bill_calculation["total_amount_with_gst"] or 0
        total_gst = bill_calculation["total_gst"] or 0
        total_amount = round(total_amount_with_gst, 2) - round(total_gst, 2)

        q_total_amount_with_gst = quotation_calculations["q_total_amount_with_gst"] or 0
        q_total_gst = quotation_calculations["q_total_gst"] or 0
        q_total_amount = q_total_amount_with_gst - q_total_gst

        # --- Response ---
        return Response(
            {
                "bill": bill_count,
                "quotation": quotation_count,
                "party": party_count,
                "total_amount_with_gst": total_amount_with_gst,
                "total_gst": total_gst,
                "total_amount": total_amount,
                "q_total_amount_with_gst": q_total_amount_with_gst,
                "q_total_gst": q_total_gst,
                "q_total_amount": q_total_amount,
                "from_date": from_date,
                "to_date": to_date,
                "is_paid": is_paid,
            }
        )


class BillQuotationCountView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        user = request.user
        year = date.today().year - 1

        # --- Aggregate bills by month ---
        bills_by_month = (
            BillDetail.objects.filter(date__year=year, party__user=user)
            .annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        bills_dict = {item["month"]: item["count"] for item in bills_by_month}

        # --- Aggregate quotations by month ---
        quotations_by_month = (
            QuotationDetail.objects.filter(date__year=year, party__user=user)
            .annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        quotations_dict = {item["month"]: item["count"] for item in quotations_by_month}

        # --- Prepare final data ---
        data = [
            {
                "month": MONTHS[i],
                "bills": bills_dict.get(i, 0),
                "quotation": quotations_dict.get(i, 0),
            }
            for i in range(1, 13)
        ]

        return Response({"data": data})


class BillGstAmountView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        user = request.user
        current_date = timezone.now()

        # Get start of financial year
        financial_year_start = timezone.make_aware(
            timezone.datetime(current_date.year, 4, 1)
        )
        if current_date < financial_year_start:
            financial_year_start = timezone.make_aware(
                timezone.datetime(current_date.year - 1, 4, 1)
            )

        # Aggregate bills and GST per month
        qs = (
            BillDetail.objects.filter(date__gte=financial_year_start, party__user=user)
            .annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(
                bill_amount=Sum("total_amount_after_gst"),
                gst_amount=Sum("total_gst_amount"),
            )
        )

        amounts = {row["month"]: row for row in qs}

        # Build response for all 12 months
        data = [
            {
                "month": MONTHS[i],
                "bill_amount": amounts.get(i, {}).get("bill_amount") or 0,
                "gst_amount": amounts.get(i, {}).get("gst_amount") or 0,
            }
            for i in range(1, 13)
        ]

        return Response({"data": data})


class Top5Clients(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        end_date, start_date = get_current_financial_date()
        user = request.user

        # Aggregate bills directly by client
        top_clients = (
            BillDetail.objects.filter(
                date__range=(start_date, end_date), party__user=user
            )
            .values("party__id", "party__name")
            .annotate(amount=Sum("total_amount_after_gst"))
            .order_by("-amount")[:5]
        )
        # Normalize result
        data = [
            {"name": c["party__name"], "amount": int(c["amount"] or 0)}
            for c in top_clients
        ]

        return Response({"data": data})


class TotalPaidUnpaid(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        end_date, start_date = get_current_financial_date()
        print(f"Showing from {start_date} to {end_date}")

        qs = BillDetail.objects.filter(date__range=(start_date, end_date))

        result = qs.aggregate(
            total=Sum("total_amount_after_gst", output_field=FloatField()),
            paid=Sum(
                Case(
                    When(is_paid=True, then=F("total_amount_after_gst")),
                    default=0,
                    output_field=FloatField(),
                )
            ),
        )

        total = result["total"] or 0.0
        paid = result["paid"] or 0.0
        pending = total - paid

        data = [
            {"name": "Total", "amount": total},
            {"name": "Received", "amount": paid},
            {"name": "Pending", "amount": pending},
        ]

        return Response({"data": data})
