from rest_framework import serializers
from django.db import transaction
from sales.models import QuotationDetail, BillDetail, ProductDetail
from clients.serializers import ClientSerializer
from django.contrib.contenttypes.models import ContentType


from clients.models import Client

from django.contrib.contenttypes.models import ContentType



class ProductDetailSerializer(serializers.ModelSerializer):
    gst_rate = serializers.ReadOnlyField()
    get_sgst_amount = serializers.ReadOnlyField()
    get_cgst_amount = serializers.ReadOnlyField()
    get_igst_amount = serializers.ReadOnlyField()
    single_item_total_gst = serializers.ReadOnlyField()
    single_item_total_amount_without_tax = serializers.ReadOnlyField()
    single_item_total_amount_after_tax = serializers.ReadOnlyField()

    class Meta:
        model = ProductDetail
        exclude = ("content_type", "object_id")

    def validate_product_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value


class BaseTransactionSerializer(serializers.ModelSerializer):

    party = ClientSerializer(read_only=True)
    party_id = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), source="party", write_only=True, required=True
    )
    products = ProductDetailSerializer(many=True)

    class Meta:
        abstract = True

    def _save_products(self, instance, products_data):
        content_type = ContentType.objects.get_for_model(instance.__class__)

        ProductDetail.objects.filter(
            content_type=content_type, object_id=instance.id
        ).delete()

        ProductDetail.objects.bulk_create(
            [
                ProductDetail(content_type=content_type, object_id=instance.id, **prd)
                for prd in products_data
            ]
        )

    def create(self, validated_data):
        products_data = validated_data.pop("products", [])

        with transaction.atomic():
            instance = self.Meta.model.objects.create(**validated_data)
            self._save_products(instance, products_data)
            instance.update_totals()

        return instance

    def update(self, instance, validated_data):
        products_data = validated_data.pop("products", [])

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if products_data:
                self._save_products(instance, products_data)

            instance.update_totals()

        return instance

    def validate(self, attrs):
        """
        Ensure at least one product is provided on create
        """
        request = self.context.get("request")

        # Create request (POST)
        if request and request.method == "POST":
            products = attrs.get("products")
            if not products:
                raise serializers.ValidationError(
                    {"products": "At least one product is required."}
                )

        return attrs


class QuotationSerializer(BaseTransactionSerializer):

    class Meta:
        model = QuotationDetail
        fields = "__all__"


class BillSerializer(BaseTransactionSerializer):

    class Meta:
        model = BillDetail
        fields = "__all__"


class InvoiceFromQuotationSerializer(serializers.Serializer):
    quotation_id = serializers.IntegerField()

    def create(self, validated_data):
        quotation = QuotationDetail.objects.get(id=validated_data["quotation_id"])

        invoice = BillDetail.objects.create(
            party=quotation.party,
            billno=generate_bill_no(),
            date=datetime.now(),
        )

        ProductDetail.objects.bulk_create(
            [
                ProductDetail(
                    content_type=ContentType.objects.get_for_model(BillDetail),
                    object_id=invoice.id,
                    hsncode=p.hsncode,
                    cgst=p.cgst,
                    sgst=p.sgst,
                    igst=p.igst,
                    product_discription=p.product_discription,
                    product_quantity=p.product_quantity,
                    unit_type=p.unit_type,
                    unit_price=p.unit_price,
                )
                for p in quotation.products.all()
            ]
        )

        invoice.update_totals()
        return invoice
