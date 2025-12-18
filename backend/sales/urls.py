from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import QuotationViewSet, BillDetailViewSet

router = DefaultRouter()
router.register(r"quotations", QuotationViewSet, basename="quotation")
router.register(r"invoices", BillDetailViewSet, basename="invoices")

urlpatterns = [
    path("", include(router.urls)),
]
