from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import QuotationViewSet, BillViewSet

router = DefaultRouter()
router.register(r"quotations", QuotationViewSet, basename="quotation")
router.register(r"invoices", BillViewSet, basename="invoices")

urlpatterns = [
    path("", include(router.urls)),
]
