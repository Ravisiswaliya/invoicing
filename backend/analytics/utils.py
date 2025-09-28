from django.db.models import Sum, F, FloatField, ExpressionWrapper, Count
from decimal import Decimal


def bill_annotations():
    return {
        "total_igst": ExpressionWrapper(
            Sum(
                F("productdetails__igst")
                * F("productdetails__unit_price")
                * F("productdetails__product_quantity")
            ),
            output_field=FloatField(),
        )
        / 100,
        "total_sgst": ExpressionWrapper(
            Sum(
                F("productdetails__sgst")
                * F("productdetails__unit_price")
                * F("productdetails__product_quantity")
            ),
            output_field=FloatField(),
        )
        / 100,
        "total_cgst": ExpressionWrapper(
            Sum(
                F("productdetails__cgst")
                * F("productdetails__unit_price")
                * F("productdetails__product_quantity")
            ),
            output_field=FloatField(),
        )
        / 100,
        "total_amount_without_gst": ExpressionWrapper(
            Sum(
                F("productdetails__unit_price") * F("productdetails__product_quantity")
            ),
            output_field=FloatField(),
        ),
        "total_amount": ExpressionWrapper(
            Sum(
                F("productdetails__unit_price")
                * F("productdetails__product_quantity")
                * (
                    F("productdetails__igst") / Decimal("100")
                    + F("productdetails__cgst") / Decimal("100")
                    + F("productdetails__sgst") / Decimal("100")
                    + Decimal("1")
                )
            ),
            output_field=FloatField(),
        ),
    }
