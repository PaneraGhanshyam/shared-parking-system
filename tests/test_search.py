from django.test import TestCase
from django.utils import timezone
import datetime
from tests.helpers import create_user, create_space, authenticated_client
from reservations.models import Reservation

class AvailabilitySearchTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = authenticated_client(self.user)
        self.space = create_space()

        self.start = timezone.now().replace(microsecond=0) + datetime.timedelta(days=1)
        self.end = self.start + datetime.timedelta(hours=2)

    def format_dt(self, dt):
        """Format datetime as UTC ISO 8601 string ending with 'Z'."""
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def test_space_is_available_when_no_reservations_exist(self):
        response = self.client.get(
           f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_booked_space_is_excluded(self):
        Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.start,
            end_time=self.end,
            total_price=50.00,
            status="CONFIRMED"
        )
        response = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_unauthenticated_request_returns_401(self):
        from rest_framework.test import APIClient
        anonymous_client = APIClient()
        response = anonymous_client.get(
                f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}"
            )
        self.assertEqual(response.status_code, 401)

    def test_missing_parameters_returns_400(self):
        response = self.client.get("/api/spaces/available/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.data)

    def test_end_before_or_equal_to_start_returns_400(self):
        bad_end = self.start - datetime.timedelta(hours=1)
        response = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(bad_end)}"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("end", response.data["errors"])

    def test_adjacent_boundary_window_includes_space(self):
        Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.start,
            end_time=self.end,
            total_price=50.00,
            status="CONFIRMED",
        )
        next_start = self.end
        next_end = self.end + datetime.timedelta(hours=2)
        response = self.client.get(f"/api/spaces/available/?start={self.format_dt(next_start)}&end={self.format_dt(next_end)}"
    )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_cancelled_reservation_does_not_block_space(self):
        Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.start,
            end_time=self.end,
            total_price=50.00,
            status="CANCELLED",
        )
        response = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_inactive_space_is_excluded(self):
        self.space.soft_delete()
        response = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_cancelling_reservation_makes_space_available(self):
        reservation = Reservation.objects.create(
            user=self.user,
            space=self.space,
            start_time=self.start,
            end_time=self.end,
            total_price=50.00,
            status=Reservation.Status.CONFIRMED,
        )

        search_url = (
            f"/api/spaces/available/?start={self.format_dt(self.start)}"
            f"&end={self.format_dt(self.end)}"
        )

        response = self.client.get(search_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        cancel_response = self.client.post(
            f"/api/reservations/{reservation.id}/cancel/"
        )

        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(
            cancel_response.data["status"],
            Reservation.Status.CANCELLED,
        )

        search_response = self.client.get(search_url)

        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.data["count"], 1)

    def test_filter_by_city_case_insensitive(self):
        response = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&city=ahmedabad"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

        response_surat = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&city=Surat"
        )
        self.assertEqual(response_surat.status_code, 200)
        self.assertEqual(response_surat.data["count"], 0)

    def test_filter_by_vehicle_type(self):
        response_car = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&vehicle_type=CAR"
        )
        self.assertEqual(response_car.status_code, 200)
        self.assertEqual(response_car.data["count"], 1)

        response_truck = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&vehicle_type=TRUCK"
        )
        self.assertEqual(response_truck.status_code, 200)
        self.assertEqual(response_truck.data["count"], 0)

    def test_filter_by_max_price(self):
        response_cheap = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&max_price=10.00"
        )
        self.assertEqual(response_cheap.status_code, 200)
        self.assertEqual(response_cheap.data["count"], 0)

        response_sufficient = self.client.get(
            f"/api/spaces/available/?start={self.format_dt(self.start)}&end={self.format_dt(self.end)}&max_price=100.00"
        )
        self.assertEqual(response_sufficient.status_code, 200)
        self.assertEqual(response_sufficient.data["count"], 1)

