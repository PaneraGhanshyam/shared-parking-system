import datetime
from decimal import Decimal

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from reservations.admin import ReservationAdmin
from reservations.models import Reservation
from tests.helpers import (
    authenticated_client,
    create_property,
    create_space,
    create_user,
)

User = get_user_model()


def create_reservation(
    user=None,
    space=None,
    start_time=None,
    end_time=None,
    total_price=Decimal("100.00"),
    status=Reservation.Status.CONFIRMED,
    **kwargs,
):
    """Create and return a Reservation instance for testing."""
    if user is None:
        user = create_user()
    if space is None:
        space = create_space()
    if start_time is None:
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=1)
    if end_time is None:
        end_time = start_time + datetime.timedelta(hours=2)
    return Reservation.objects.create(
        user=user,
        space=space,
        start_time=start_time,
        end_time=end_time,
        total_price=total_price,
        status=status,
        **kwargs,
    )


class ReservationQuerySetTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.space = create_space()

        # Fixed reference point in the future (without microseconds)
        self.base_time = timezone.now().replace(microsecond=0) + datetime.timedelta(
            days=2
        )
        # Reference reservation interval: [10:00, 12:00]
        self.res_start = self.base_time + datetime.timedelta(hours=10)
        self.res_end = self.base_time + datetime.timedelta(hours=12)

        self.existing_res = create_reservation(
            user=self.user,
            space=self.space,
            start_time=self.res_start,
            end_time=self.res_end,
            status=Reservation.Status.CONFIRMED,
        )

    def test_confirmed_includes_confirmed_and_excludes_cancelled(self):
        cancelled_res = create_reservation(
            user=self.user,
            space=self.space,
            status=Reservation.Status.CANCELLED,
        )
        qs = Reservation.objects.confirmed()
        self.assertIn(self.existing_res, qs)
        self.assertNotIn(cancelled_res, qs)

    def test_overlapping_detects_identical_intervals(self):
        qs = Reservation.objects.overlapping(self.res_start, self.res_end)
        self.assertIn(self.existing_res, qs)

    def test_overlapping_detects_partial_overlap_at_start(self):
        # Requested interval starts before and ends inside [09:00, 11:00]
        req_start = self.base_time + datetime.timedelta(hours=9)
        req_end = self.base_time + datetime.timedelta(hours=11)
        qs = Reservation.objects.overlapping(req_start, req_end)
        self.assertIn(self.existing_res, qs)

    def test_overlapping_detects_partial_overlap_at_end(self):
        # Requested interval starts inside and ends after [11:00, 13:00]
        req_start = self.base_time + datetime.timedelta(hours=11)
        req_end = self.base_time + datetime.timedelta(hours=13)
        qs = Reservation.objects.overlapping(req_start, req_end)
        self.assertIn(self.existing_res, qs)

    def test_overlapping_detects_when_existing_interval_encloses_requested(self):
        # Requested interval is strictly inside [10:30, 11:30]
        req_start = self.base_time + datetime.timedelta(hours=10, minutes=30)
        req_end = self.base_time + datetime.timedelta(hours=11, minutes=30)
        qs = Reservation.objects.overlapping(req_start, req_end)
        self.assertIn(self.existing_res, qs)

    def test_overlapping_detects_when_requested_interval_encloses_existing(self):
        # Requested interval encloses the existing [09:00, 13:00]
        req_start = self.base_time + datetime.timedelta(hours=9)
        req_end = self.base_time + datetime.timedelta(hours=13)
        qs = Reservation.objects.overlapping(req_start, req_end)
        self.assertIn(self.existing_res, qs)

    def test_overlapping_allows_boundary_touching_intervals(self):
        # Requested ends exactly when existing starts [08:00, 10:00]
        touching_start_begin = self.base_time + datetime.timedelta(hours=8)
        touching_start_end = self.res_start
        qs_start_touch = Reservation.objects.overlapping(
            touching_start_begin, touching_start_end
        )
        self.assertNotIn(self.existing_res, qs_start_touch)

        # Requested starts exactly when existing ends [12:00, 14:00]
        touching_end_begin = self.res_end
        touching_end_finish = self.base_time + datetime.timedelta(hours=14)
        qs_end_touch = Reservation.objects.overlapping(
            touching_end_begin, touching_end_finish
        )
        self.assertNotIn(self.existing_res, qs_end_touch)

    def test_overlapping_excludes_completely_disjoint_intervals(self):
        # Completely before [06:00, 08:00]
        before_start = self.base_time + datetime.timedelta(hours=6)
        before_end = self.base_time + datetime.timedelta(hours=8)
        qs_before = Reservation.objects.overlapping(before_start, before_end)
        self.assertNotIn(self.existing_res, qs_before)

        # Completely after [14:00, 16:00]
        after_start = self.base_time + datetime.timedelta(hours=14)
        after_end = self.base_time + datetime.timedelta(hours=16)
        qs_after = Reservation.objects.overlapping(after_start, after_end)
        self.assertNotIn(self.existing_res, qs_after)

    def test_confirmed_overlapping_can_be_chained(self):
        cancelled_res = create_reservation(
            user=self.user,
            space=self.space,
            start_time=self.res_start,
            end_time=self.res_end,
            status=Reservation.Status.CANCELLED,
        )
        # Chained query: only confirmed overlapping reservations returned
        chained_qs = Reservation.objects.confirmed().overlapping(
            self.res_start, self.res_end
        )
        self.assertIn(self.existing_res, chained_qs)
        self.assertNotIn(cancelled_res, chained_qs)

        # Raw overlapping without confirmed() includes both
        raw_qs = Reservation.objects.overlapping(self.res_start, self.res_end)
        self.assertIn(self.existing_res, raw_qs)
        self.assertIn(cancelled_res, raw_qs)

    def test_str_representation(self):
        self.assertEqual(
            str(self.existing_res),
            f"Reservation {self.existing_res.id} - {self.space} (CONFIRMED)",
        )


class ReservationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = create_user(username="user1", email="user1@example.com")
        self.user2 = create_user(username="user2", email="user2@example.com")
        self.space = create_space()

        self.res1 = create_reservation(user=self.user1, space=self.space)
        self.res2 = create_reservation(user=self.user1, space=self.space)
        self.res_other = create_reservation(user=self.user2, space=self.space)

        self.auth_client = authenticated_client(user=self.user1)

    def test_unauthenticated_get_list_returns_401(self):
        response = self.client.get("/api/reservations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_returns_only_current_user_reservations(self):
        response = self.auth_client.get("/api/reservations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 2)
        returned_ids = {item["id"] for item in results}
        self.assertEqual(returned_ids, {self.res1.id, self.res2.id})
        self.assertNotIn(self.res_other.id, returned_ids)

    def test_user_can_retrieve_own_reservation_with_nested_space_info(self):
        response = self.auth_client.get(f"/api/reservations/{self.res1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.res1.id)

        self.assertIn("space", response.data)
        space_data = response.data["space"]
        self.assertIsInstance(space_data, dict)
        self.assertEqual(space_data["id"], self.space.id)
        self.assertEqual(space_data["spot_label"], self.space.spot_label)
        self.assertEqual(space_data["vehicle_type"], self.space.vehicle_type)
        self.assertEqual(
            space_data["property_title"],
            self.space.parking_property.title,
        )
        self.assertEqual(
            space_data["address"],
            self.space.parking_property.address,
        )
        self.assertEqual(space_data["city"], self.space.parking_property.city)

    def test_user_cannot_retrieve_another_user_reservation_id(self):
        # Uses another user's actual reservation ID, not their user ID
        response = self.auth_client.get(f"/api/reservations/{self.res_other.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expected_response_fields_and_data(self):
        response = self.auth_client.get(f"/api/reservations/{self.res1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = {
            "id",
            "user",
            "space",
            "start_time",
            "end_time",
            "total_price",
            "status",
            "created_at",
            "cancelled_at",
        }
        self.assertEqual(set(response.data.keys()), expected_fields)
        self.assertEqual(response.data["user"], self.user1.id)
        self.assertEqual(response.data["total_price"], str(self.res1.total_price))
        self.assertEqual(response.data["status"], "CONFIRMED")
        self.assertIsNone(response.data["cancelled_at"])

    def test_create_reservation_requires_fields(self):
        response = self.auth_client.post("/api/reservations/", {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

    def test_create_reservation_successfully(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=response.data["id"])

        self.assertEqual(reservation.user, self.user1)
        self.assertEqual(reservation.space, self.space)
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

        expected_price = self.space.price_per_hour * Decimal("2")
        self.assertEqual(reservation.total_price, expected_price)

    def test_create_reservation_rejects_overlapping_booking(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        # Another customer already booked this space.
        create_reservation(
            user=self.user2,
            space=self.space,
            start_time=start_time,
            end_time=end_time,
        )

        # Current customer tries to book the same time slot.
        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "This time slot is already booked.",
        )

    def test_create_reservation_allows_adjacent_time_slot(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        existing_end = start_time + datetime.timedelta(hours=2)
        new_end = existing_end + datetime.timedelta(hours=2)

        create_reservation(
            user=self.user2,
            space=self.space,
            start_time=start_time,
            end_time=existing_end,
        )

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": existing_end.isoformat(),
                "end_time": new_end.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_reservation_rejects_own_space(self):
        own_property = create_property(owner=self.user1)
        own_space = create_space(parking_property=own_property)

        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": own_space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    def test_create_reservation_allows_previously_cancelled_slot(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        create_reservation(
            user=self.user2,
            space=self.space,
            start_time=start_time,
            end_time=end_time,
            status=Reservation.Status.CANCELLED,
        )

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    def test_create_reservation_rejects_past_start_time(self):
        start_time = timezone.now() - datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    def test_create_reservation_rejects_end_before_start(self):
        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time - datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_rejects_missing_space(self):
        missing_space_id = self.space.id + 999

        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": missing_space_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reservation_rejects_inactive_space(self):
        self.space.is_active = False
        self.space.save(update_fields=["is_active"])

        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reservation_rejects_inactive_property(self):
        parking_property = self.space.parking_property
        parking_property.is_active = False
        parking_property.save(update_fields=["is_active"])

        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reservation_rejects_inactive_property_owner(self):
        owner = self.space.parking_property.owner
        owner.is_active = False
        owner.save(update_fields=["is_active"])

        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_user_cannot_create_reservation(self):
        start_time = timezone.now() + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_reservation_calculates_partial_hour_price(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(minutes=90)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=response.data["id"])

        expected_price = (
            self.space.price_per_hour * Decimal("1.5")
        ).quantize(Decimal("0.01"))

        self.assertEqual(reservation.total_price, expected_price)
    def test_create_reservation_ignores_client_supplied_price(self):
        start_time = timezone.now().replace(microsecond=0) + datetime.timedelta(days=5)
        end_time = start_time + datetime.timedelta(hours=2)

        response = self.auth_client.post(
            "/api/reservations/",
            {
                "space": self.space.id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_price": "1.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=response.data["id"])

        expected_price = self.space.price_per_hour * Decimal("2")

        self.assertEqual(reservation.total_price, expected_price)
        self.assertNotEqual(reservation.total_price, Decimal("1.00"))
    def test_cancel_extension_slot_returns_501(self):
        response = self.auth_client.post(f"/api/reservations/{self.res1.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_authenticated_get_list_deterministic_ordering(self):
        res3 = create_reservation(user=self.user1, space=self.space)
        response = self.auth_client.get("/api/reservations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = (
            response.data["results"]
            if "results" in response.data
            else response.data
        )
        returned_ids = [item["id"] for item in results]
        expected_ids = list(
            Reservation.objects.filter(user=self.user1)
            .order_by("-created_at", "-id")
            .values_list("id", flat=True)
        )
        self.assertEqual(returned_ids, expected_ids)
        self.assertEqual(len(returned_ids), 3)
        self.assertEqual(returned_ids[0], res3.id)


class ReservationConstraintTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.space = create_space()
        self.now = timezone.now().replace(microsecond=0) + datetime.timedelta(days=1)

    def test_reservation_cannot_be_saved_when_start_time_equals_end_time(self):
        with self.assertRaises(IntegrityError):
            Reservation.objects.create(
                user=self.user,
                space=self.space,
                start_time=self.now,
                end_time=self.now,
                total_price=Decimal("50.00"),
                status=Reservation.Status.CONFIRMED,
            )

    def test_reservation_cannot_be_saved_when_start_time_after_end_time(self):
        with self.assertRaises(IntegrityError):
            Reservation.objects.create(
                user=self.user,
                space=self.space,
                start_time=self.now + datetime.timedelta(hours=2),
                end_time=self.now,
                total_price=Decimal("50.00"),
                status=Reservation.Status.CONFIRMED,
            )

    def test_reservation_cannot_be_saved_with_negative_total_price(self):
        with self.assertRaises(IntegrityError):
            Reservation.objects.create(
                user=self.user,
                space=self.space,
                start_time=self.now,
                end_time=self.now + datetime.timedelta(hours=2),
                total_price=Decimal("-1.00"),
                status=Reservation.Status.CONFIRMED,
            )

    def test_valid_reservation_with_zero_price_can_be_saved(self):
        res = Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.now,
            end_time=self.now + datetime.timedelta(hours=2),
            total_price=Decimal("0.00"),
            status=Reservation.Status.CONFIRMED,
        )
        self.assertIsNotNone(res.id)
        self.assertEqual(res.total_price, Decimal("0.00"))

    def test_valid_reservation_with_positive_price_can_be_saved(self):
        res = Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.now,
            end_time=self.now + datetime.timedelta(hours=2),
            total_price=Decimal("75.50"),
            status=Reservation.Status.CONFIRMED,
        )
        self.assertIsNotNone(res.id)
        self.assertEqual(res.total_price, Decimal("75.50"))


class ReservationAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = ReservationAdmin(Reservation, self.site)
        self.factory = RequestFactory()

    def test_reservation_admin_has_delete_permission_returns_false(self):
        request = self.factory.get("/admin/")
        request.user = create_user(is_staff=True, is_superuser=True)
        res = create_reservation()

        self.assertFalse(self.admin.has_delete_permission(request))
        self.assertFalse(self.admin.has_delete_permission(request, obj=res))
