from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter


class BaseTransactionFilter(filters.FilterSet):
    """
    Generic filter for models with:
    - party relation
    - date field
    - total_amount_after_gst field
    Supports icontains, ranges, and optional user filtering.
    """

    # Party name partial match
    party = filters.CharFilter(field_name="party__name", lookup_expr="icontains")

    # Date range
    date_after = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateFilter(field_name="date", lookup_expr="lte")

    # Amount range
    min_amount = filters.NumberFilter(
        field_name="total_amount_after_gst", lookup_expr="gte"
    )
    max_amount = filters.NumberFilter(
        field_name="total_amount_after_gst", lookup_expr="lte"
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Optional user-based party filtering
        if self.request and self.request.user.is_authenticated:
            party_filter = self.filters.get("party")
            if (
                party_filter
                and hasattr(party_filter.field, "queryset")
                and party_filter.field.queryset is not None
            ):
                party_filter.field.queryset = party_filter.field.queryset.filter(
                    user=self.request.user
                )


# Specialized filters for Bills and Quotations
class BillFilter(BaseTransactionFilter):
    class Meta:
        model = None  # assign dynamically in the ViewSet
        fields = [
            "party",
            "billno",
            "date",
            "date_after",
            "date_before",
            "total_amount_after_gst",
            "min_amount",
            "max_amount",
        ]


class QuotationFilter(BaseTransactionFilter):
    class Meta:
        model = None  # assign dynamically in the ViewSet
        fields = [
            "party",
            "quotationno",
            "date",
            "date_after",
            "date_before",
            "total_amount_after_gst",
            "min_amount",
            "max_amount",
        ]
