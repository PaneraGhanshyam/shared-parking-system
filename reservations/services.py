
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from config.exceptions import SlotUnavailableError
from spaces.models import Space

from .models import Reservation


@transaction.atomic
def create_reservation(user, space, start_time, end_time):

    # 1. Validate the time range
    if start_time <= timezone.now():
        raise ValidationError({
            "start_time": "Start time must be in the future."
        })

    if end_time <= start_time:
        raise ValidationError({
            "end_time": "End time must be after start time."
        })

    # 2. Lock the requested active space
    try:
        locked_space = (
            Space.objects.active()
            .select_for_update(of=("self",))
            .get(pk=space.pk)
        )
    except Space.DoesNotExist:
        raise NotFound("Space not found or inactive.")

    # 3. Prevent users from booking their own space
    if locked_space.parking_property.owner_id == user.id:
        raise ValidationError(
            "You cannot reserve your own space."
        )

    # 4. Check for an existing overlapping confirmed reservation
    overlapping_reservation = (
        Reservation.objects.confirmed()
        .overlapping(start_time, end_time)
        .filter(space=locked_space)
        .exists()
    )

    if overlapping_reservation:
        raise SlotUnavailableError()

    # 5. Calculate the total booking price
    duration_seconds = Decimal(
        str((end_time - start_time).total_seconds())
    )
    hours = duration_seconds / Decimal("3600")

    total_price = (
        hours * locked_space.price_per_hour
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # 6. Create the reservation
    reservation = Reservation.objects.create(
        user=user,
        space=locked_space,
        start_time=start_time,
        end_time=end_time,
        total_price=total_price,
        status=Reservation.Status.CONFIRMED,
    )

    return reservation


def cancel_reservation(user, reservation_id):
    pass
