from django.contrib import admin
from .models import ParkingProperty, Space

@admin.register(ParkingProperty)
class ParkingPropertyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "city", "owner", "is_active")
    list_filter = ("is_active", "city", "state")
    search_fields = ("title", "address", "city", "owner__username")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "spot_label",
        "parking_property",
        "vehicle_type",
        "price_per_hour",
        "is_active",
    )
    list_filter = ("vehicle_type", "is_active")
    search_fields = ("spot_label", "parking_property__title")

    def has_delete_permission(self, request, obj=None):
        return False
