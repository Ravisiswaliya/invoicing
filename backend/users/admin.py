from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, Verification


class AccountAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "date_joined",
        "last_login",
        "is_superuser",
    )
    search_fields = ("username", "email")
    readonly_fields = ("date_joined", "last_login")

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(Verification)
