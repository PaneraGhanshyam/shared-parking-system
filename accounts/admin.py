from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin with soft delete policy: delete permission is disabled.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("phone_number", "deleted_at")}),
    )
    list_display = BaseUserAdmin.list_display + ("phone_number", "deleted_at")

    def has_delete_permission(self, request, obj=None):
        return False
