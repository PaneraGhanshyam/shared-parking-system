
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
            .get(pk=space)
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


@transaction.atomic
def cancel_reservation(user, reservation_id):
    # 1. Find the reservation and lock it.
    # Filter by user to avoid revealing another user's reservation.
    try:
        reservation = (
            Reservation.objects
            .select_for_update()
            .get(pk=reservation_id, user=user)
        )
    except Reservation.DoesNotExist:
        raise NotFound("Reservation not found.")

    # 2. Only confirmed reservations can be cancelled.
    if reservation.status != Reservation.Status.CONFIRMED:
        raise ValidationError("Reservation is already cancelled.")

    # 3. Cancellation is allowed only before the reservation starts.
    now = timezone.now()

    if now >= reservation.start_time:
        raise ValidationError(
            "Cannot cancel a reservation that has already started."
        )

    # 4. Update the reservation to release the slot.
    reservation.status = Reservation.Status.CANCELLED
    reservation.cancelled_at = now

    reservation.save(
        update_fields=["status", "cancelled_at"]
    )

    return reservation
