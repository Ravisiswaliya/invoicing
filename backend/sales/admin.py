from django.contrib import admin
from sales.models import QuotationDetail, BillDetail, ProductDetail

# Register your models here.
admin.site.register(QuotationDetail)
admin.site.register(BillDetail)
admin.site.register(ProductDetail)


# data = {
#     "products": [
#         {
#             "hsncode": 1001,
#             "cgst": Decimal("9.00"),
#             "sgst": Decimal("9.00"),
#             "igst": Decimal("0.00"),
#             "product_discription": "Widget A",
#             "product_quantity": 10,
#             "unit_type": "PCS",
#             "unit_price": Decimal("50.00"),
#         },
#         {
#             "hsncode": 1002,
#             "cgst": Decimal("0.00"),
#             "sgst": Decimal("0.00"),
#             "igst": Decimal("18.00"),
#             "product_discription": "Gadget B",
#             "product_quantity": 5,
#             "unit_type": "PCS",
#             "unit_price": Decimal("100.00"),
#         },
#     ],
#     "orderno": "ORD-2025-001",
#     "billno": "INV-2025-001",
#     "date": datetime.date(2025, 9, 21),
#     "transportmode": "Road",
#     "vehicleno": "HR20AB1234",
#     "dateofsupply": datetime.date(2025, 9, 21),
#     "placeofsupply": "Delhi",
#     "gstrc": 0,
#     "tc": "Custom T&C if different",
#     "is_paid": False,
# }
