from rest_framework import serializers
from django.db import transaction
from sales.models import QProductDetail, QuotationDetail
from clients.serializers import ClientSerializer
from sales.models import BillDetail, ProductDetail

from clients.models import Client


class BaseProductSerializer(serializers.ModelSerializer):
    get_sgst_amount = serializers.ReadOnlyField()
    get_cgst_amount = serializers.ReadOnlyField()
    get_igst_amount = serializers.ReadOnlyField()
    single_item_total_gst = serializers.ReadOnlyField()
    get_gst_prctg = serializers.ReadOnlyField()
    single_item_total_amount_without_tax = serializers.ReadOnlyField()
    single_item_total_amount_after_tax = serializers.ReadOnlyField()

    class Meta:
        abstract = True
        fields = [
            "hsncode",
            "cgst",
            "sgst",
            "igst",
            "product_discription",
            "product_quantity",
            "unit_type",
            "unit_price",
            "get_sgst_amount",
            "get_cgst_amount",
            "get_igst_amount",
            "single_item_total_gst",
            "get_gst_prctg",
            "single_item_total_amount_without_tax",
            "single_item_total_amount_after_tax",
        ]


class ProductDetailSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        model = ProductDetail


class QProductDetailSerializer(BaseProductSerializer):
    class Meta(BaseProductSerializer.Meta):
        model = QProductDetail


class BaseTransactionSerializer(serializers.ModelSerializer):
    party = ClientSerializer(read_only=True)
    party_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source="party", write_only=True
    )

    total_gst_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total_amount_after_gst = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    total_units = serializers.CharField(read_only=True)

    product_field = None  # override in child
    product_model = None  # override in child
    related_name = None  # override in child
    nested_serializer = None  # override in child

    class Meta:
        abstract = True

    def create(self, validated_data):
        products_data = validated_data.pop(self.related_name, [])
        with transaction.atomic():
            instance = self.Meta.model.objects.create(**validated_data)
            self._create_or_update_products(instance, products_data)
        return instance

    def update(self, instance, validated_data):
        products_data = validated_data.pop(self.related_name, [])
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if products_data:
                self.product_model.objects.filter(
                    **{self.product_field: instance}
                ).delete()
                self._create_or_update_products(instance, products_data)

        instance.refresh_from_db()
        instance.update_totals()
        return instance

    def _create_or_update_products(self, instance, product_data):
        for prd in products_data:
            self.product_model.objects.create(**{self.product_field: instance}, **prd)


class BillDetailSerializer(BaseTransactionSerializer):
    productdetails = ProductDetailSerializer(many=True, required=False)

    class Meta(BaseTransactionSerializer.Meta):
        model = BillDetail
        fields = [
            "id",
            "party",
            "party_id",
            "orderno",
            "billno",
            "date",
            "transportmode",
            "vehicleno",
            "dateofsupply",
            "placeofsupply",
            "gstrc",
            "tc",
            "is_paid",
            "total_gst_amount",
            "total_amount_after_gst",
            "total_units",
            "productdetails",
        ]

    product_field = "billno"
    product_model = ProductDetail
    related_name = "productdetails"
    nested_serializer = ProductDetailSerializer


class QuotationDetailSerializer(BaseTransactionSerializer):
    quotationdetails = QProductDetailSerializer(many=True, required=False)

    class Meta(BaseTransactionSerializer.Meta):
        model = QuotationDetail
        fields = [
            "id",
            "party",
            "party_id",
            "quotationno",
            "date",
            "subject",
            "tc",
            "total_gst_amount",
            "total_amount_after_gst",
            "total_units",
            "quotationdetails",
        ]

    product_field = "quotationno"
    product_model = QProductDetail
    related_name = "quotationdetails"
    nested_serializer = QProductDetailSerializer
