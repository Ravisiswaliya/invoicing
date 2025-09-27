from django.db import models


class BillManager(models.Manager):

    def get_unpaid_bill_amount(self, column_name, start_date, end_date):
        queryset = self.filter(is_paid=False, date__gte=start_date, date__lte=end_date)
        return queryset.aggregate(unpaid_bill_amount=models.Sum(column_name))[
            "unpaid_bill_amount"
        ]

    def get_paid_bill_amount(self, column_name, start_date, end_date):
        queryset = self.filter(is_paid=True, date__gte=start_date, date__lte=end_date)
        return queryset.aggregate(paid_bill_amount=models.Sum(column_name))[
            "paid_bill_amount"
        ]

    def get_total_bill_amount_with_gst(self, start_date, end_date):
        queryset = self.filter(is_paid=False, date__gte=start_date, date__lte=end_date)
        return queryset.aggregate(
            total_bill_amount_with_gst=models.Sum("total_amount_after_gst")
        )["total_bill_amount_with_gst"]

    def get_total_bill_amount_without_gst(self, start_date, end_date):
        queryset = self.filter(is_paid=False, date__gte=start_date, date__lte=end_date)
        return queryset.aggregate(
            total__bill_gst_amount=models.Sum("total_gst_amount")
        )["total__bill_gst_amount"]
