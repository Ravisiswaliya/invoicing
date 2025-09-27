from datetime import datetime
from decimal import Decimal
from django.db import models

from clients.models import Client
from .manager import BillManager
from django.db.models import F, Sum, DecimalField, ExpressionWrapper

UNIT_TYPES = (
    ("BAG", "BAGS"),
    ("BAL", "BALE"),
    ("BDL", "BUNDLES"),
    ("BKL", "BUCKLES"),
    ("BOU", "BILLIONS OF UNITS"),
    ("BOX", "BOX"),
    ("BTL", "BOTTLES"),
    ("BUN", "BUNCHES"),
    ("CAN", "CANS"),
    ("CBM", "CUBIC METER"),
    ("CCM", "CUBIC CENTIMETER"),
    ("CMS", "CENTIMETER"),
    ("CTN", "CARTONS"),
    ("DOZ", "DOZEN"),
    ("DRM", "DRUM"),
    ("GGR", "GREAT GROSS"),
    ("GMS", "GRAMS"),
    ("GRS", "GROSS"),
    ("GYD", "GROSS YARDS"),
    ("KGS", "KILOGRAMS"),
    ("KLR", "KILOLITRE"),
    ("KME", "KILOMETRE"),
    ("MLT", "MILLILITRE"),
    ("MTR", "METERS"),
    ("MTS", "METRIC TON"),
    ("NOS", "NUMBERS"),
    ("PAC", "PACKS"),
    ("PCS", "PIECES"),
    ("PRS", "PAIRS"),
    ("QTL", "QUINTAL"),
    ("ROL", "ROLLS"),
    ("SET", "SETS"),
    ("SQF", "SQUARE FEET"),
    ("SQM", "SQUARE METERS"),
    ("SQY", "SQUARE YARDS"),
    ("TBS", "TABLETS"),
    ("TGM", "TEN GRAMS"),
    ("THD", "THOUSANDS"),
    ("TON", "TONNES"),
    ("TUB", "TUBES"),
    ("UGS", "US GALLONS"),
    ("UNT", "UNITS"),
    ("YDS", "YARDS"),
    ("OTH", "OTHERS"),
)


class TimeStampModel(models.Model):
    class Meta:
        abstract = True

    cdate = models.DateTimeField(auto_now=False, auto_now_add=True)
    udate = models.DateTimeField(auto_now=True, auto_now_add=False)


class BaseTransactionDetail(TimeStampModel):
    total_gst_amount = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True
    )
    total_amount_after_gst = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, blank=True
    )
    total_units = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        abstract = True

    def update_totals(self, related_name):
        products = getattr(self, related_name)

        # GST calculation: ( (cgst+sgst+igst)/100 * unit_price * quantity )
        gst_expr = ExpressionWrapper(
            (F("cgst") + F("sgst") + F("igst"))
            * F("unit_price")
            * F("product_quantity")
            / 100.0,
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        # Base amount without tax
        base_amount_expr = ExpressionWrapper(
            F("unit_price") * F("product_quantity"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )

        aggregates = products.aggregate(
            total_gst=Sum(gst_expr),
            total_units=Sum("product_quantity"),
            total_amount=Sum(base_amount_expr + gst_expr),
        )

        self.total_gst_amount = aggregates["total_gst"] or 0
        self.total_units = str(aggregates["total_units"] or 0)
        self.total_amount_after_gst = aggregates["total_amount"] or 0

        self.save(
            update_fields=["total_gst_amount", "total_amount_after_gst", "total_units"]
        )


class BillDetail(BaseTransactionDetail):
    party = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="client"
    )
    orderno = models.CharField(max_length=50, null=True, blank=True)
    billno = models.CharField(max_length=150)
    date = models.DateField(default=datetime.now)
    transportmode = models.CharField(max_length=10, null=True, blank=True)
    vehicleno = models.CharField(max_length=10, null=True, blank=True)
    dateofsupply = models.DateField(null=True, blank=True)
    placeofsupply = models.CharField(max_length=50, null=True, blank=True)
    gstrc = models.IntegerField(null=True, blank=True)
    tc = models.CharField(
        max_length=500,
        default="All Disputes subject to Hisar Jurisdiction. "
        "Goods once sold will not be taken back or exchanged. "
        "Interest @24% will be charged if bills not paid at presentation. E.& O.E.",
    )
    is_paid = models.BooleanField(default=False)

    objects = BillManager()

    def update_totals(self):
        super().update_totals("productdetails")

    def __str__(self):
        return f"{self.billno}-{self.party.name}"

    class Meta:
        db_table = "billdetails"
        ordering = ("-date", "-billno")
        get_latest_by = ["-billno"]


class QuotationDetail(BaseTransactionDetail):
    party = models.ForeignKey("clients.Client", on_delete=models.CASCADE)
    quotationno = models.IntegerField(unique=True)
    date = models.DateField(null=True, blank=True)
    subject = models.CharField(max_length=200)
    tc = models.CharField(
        max_length=1000,
        default="1. 100% ADVANCE "
        "2. Service within 7 days after order confirmation "
        "3. Quoted Rate validity is 30 Days from quotation date",
    )

    def update_totals(self):
        super().update_totals("quotationdetails")

    def __str__(self):
        return f"{self.quotationno}-{self.party.name}"

    class Meta:
        db_table = "quotaiondetails"
        ordering = ("-quotationno",)


class BaseProductDetail(TimeStampModel):
    hsncode = models.IntegerField(null=True, blank=True)
    cgst = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    sgst = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    igst = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    product_discription = models.TextField(default="")
    product_quantity = models.IntegerField(default=1)
    unit_type = models.CharField(
        max_length=3, choices=UNIT_TYPES, null=True, blank=True
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        abstract = True

    # --- Computed properties ---
    @property
    def gst_rate(self):
        return float(self.cgst + self.sgst + self.igst)

    @property
    def get_sgst_amount(self):
        return round(
            (float(self.sgst) * float(self.unit_price)) * self.product_quantity / 100, 2
        )

    @property
    def get_cgst_amount(self):
        return round(
            (float(self.cgst) * float(self.unit_price)) * self.product_quantity / 100, 2
        )

    @property
    def get_igst_amount(self):
        return round(
            (float(self.igst) * float(self.unit_price)) * self.product_quantity / 100, 2
        )

    @property
    def single_item_total_gst(self):
        return round(
            (self.gst_rate * float(self.unit_price)) * self.product_quantity / 100, 2
        )

    @property
    def single_item_total_amount_without_tax(self):
        return round(float(self.unit_price) * self.product_quantity, 2)

    @property
    def single_item_total_amount_after_tax(self):
        return round(
            self.single_item_total_amount_without_tax + self.single_item_total_gst, 2
        )


class ProductDetail(BaseProductDetail):
    billno = models.ForeignKey(
        "BillDetail", related_name="productdetails", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.billno.billno}-{self.product_discription}"

    class Meta:
        db_table = "productdetails"


class QProductDetail(BaseProductDetail):
    quotationno = models.ForeignKey(
        "QuotationDetail", related_name="quotationdetails", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.product_discription

    class Meta:
        db_table = "qproductdetails"
