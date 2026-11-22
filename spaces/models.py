
from django.conf import settings
from django.db import models
from django.utils import timezone

from .pricing import calculate_price_per_hour


class ParkingProperty(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=256)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=15, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="properties",
    )

    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["city", "is_active"],
                name="property_city_active_idx",
            ),
            models.Index(
                fields=["owner"],
                name="property_owner_idx",
            ),
        ]

    def soft_delete(self):
        now = timezone.now()

        self.is_active = False
        self.deleted_at = now
        self.save(update_fields=["is_active", "deleted_at", "updated_at"])

        self.spaces.filter(is_active=True).update(
            is_active=False,
            deleted_at=now,
            updated_at=now,
        )

    def __str__(self):
        return self.title


class SpaceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            is_active=True,
            parking_property__is_active=True,
            parking_property__owner__is_active=True,
        )


class Space(models.Model):

    class VehicleType(models.TextChoices):
        BIKE = "BIKE", "Bike"
        CAR = "CAR", "Car"
        TRUCK = "TRUCK", "Truck"

    parking_property = models.ForeignKey(
        ParkingProperty,
        on_delete=models.CASCADE,
        related_name="spaces",
    )

    spot_label = models.CharField(max_length=40)
    vehicle_type = models.CharField(
        max_length=10,
        choices=VehicleType.choices,
    )

    length_cm = models.PositiveIntegerField()
    width_cm = models.PositiveIntegerField()
    height_cm = models.PositiveIntegerField()

    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        editable=False,
    )

    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SpaceQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parking_property", "spot_label"],
                name="unique_property_spot_label",
            ),
            models.CheckConstraint(
                condition=models.Q(length_cm__gt=0),
                name="space_length_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(width_cm__gt=0),
                name="space_width_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(height_cm__gt=0),
                name="space_height_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_hour__gt=0),
                name="space_price_positive",
            ),
        ]

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at", "updated_at"])

    def save(self, *args, **kwargs):
        self.price_per_hour = calculate_price_per_hour(
            self.length_cm,
            self.width_cm,
            self.height_cm,
        )

        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = (
                set(update_fields) | {"price_per_hour", "updated_at"}
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.spot_label} - {self.vehicle_type}"
