from django.urls import include, path

from . import views

app_name = "report_api"
urlpatterns = [
    path(
        "dashboard/",
        views.DashboardAPIView.as_view(),
        name="dashboard",
    ),
    path(
        "count-bill-quotation/",
        views.BillQuotationCountView.as_view(),
        name="count-bill-gst",
    ),
    path("amount-bill-gst/", views.BillGstAmountView.as_view(), name="amount-bill-gst"),
    path("top_5_clients/", views.Top5Clients.as_view(), name="top-5-clients"),
    path(
        "total_paid_unpaid/", views.TotalPaidUnpaid.as_view(), name="total-paid-unpaid"
    ),
]
