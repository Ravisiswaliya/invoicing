from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/clients/", include("clients.urls")),
    path("api/v1/sales/", include("sales.urls")),
    path("api/v1/analytics/", include("analytics.urls")),
]
