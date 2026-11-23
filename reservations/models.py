from django.conf import settings
from django.db import models

from spaces.models import Space


class ReservationQuerySet(models.QuerySet):
    def confirmed(self):
        return self.filter(status="CONFIRMED")

    def overlapping(self, start, end):
        return self.filter(start_time__lt=end, end_time__gt=start)


class Reservation(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.PROTECT,
        related_name="reservations",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    objects = ReservationQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(
                fields=["space", "start_time", "end_time"],
                name="reservation_space_time_idx",
            ),
            models.Index(
                fields=["user", "created_at"],
                name="reservation_user_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_time__lt=models.F("end_time")),
                name="reservation_start_before_end",
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="reservation_total_price_non_negative",
            ),
        ]

    def __str__(self):
        return f"Reservation {self.id} - {self.space} ({self.status})"
