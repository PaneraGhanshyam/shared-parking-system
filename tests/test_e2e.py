import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient


class EndToEndBookingFlowTests(TestCase):
    """
    End-to-end integration test demonstrating the full lifecycle and dual-role
    nature of users (Section 6, Task Card M8 PR B).
    """

    def setUp(self):
        self.client_a = APIClient()
        self.client_b = APIClient()

    def test_full_dual_role_booking_flow(self):
        # 1. Register User A (will act as space lister) with a phone number
        reg_a_resp = self.client_a.post(
            "/api/auth/register/",
            {
                "username": "user_a",
                "email": "user_a@example.com",
                "password": "Password123!",
                "phone_number": "+919876543210",
            },
            format="json",
        )
        self.assertEqual(reg_a_resp.status_code, status.HTTP_201_CREATED)

        login_a_resp = self.client_a.post(
            "/api/auth/login/",
            {"username": "user_a", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(login_a_resp.status_code, status.HTTP_200_OK)
        token_a = login_a_resp.data["token"]
        self.client_a.credentials(HTTP_AUTHORIZATION=f"Token {token_a}")

        # 2. Register User B (will act as customer)
        reg_b_resp = self.client_b.post(
            "/api/auth/register/",
            {
                "username": "user_b",
                "email": "user_b@example.com",
                "password": "Password123!",
                "phone_number": "+919876543211",
            },
            format="json",
        )
        self.assertEqual(reg_b_resp.status_code, status.HTTP_201_CREATED)

        login_b_resp = self.client_b.post(
            "/api/auth/login/",
            {"username": "user_b", "password": "Password123!"},
            format="json",
        )
        self.assertEqual(login_b_resp.status_code, status.HTTP_200_OK)
        token_b = login_b_resp.data["token"]
        self.client_b.credentials(HTTP_AUTHORIZATION=f"Token {token_b}")

        # 3. User A creates a property and adds a CAR space of 500 x 250 x 200 cm
        prop_resp = self.client_a.post(
            "/api/properties/",
            {
                "title": "User A's Home",
                "description": "Ground floor driveway",
                "address": "12 Lake View Society",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "postal_code": "380015",
            },
            format="json",
        )
        self.assertEqual(prop_resp.status_code, status.HTTP_201_CREATED)
        property_id = prop_resp.data["id"]

        space_resp = self.client_a.post(
            "/api/spaces/",
            {
                "parking_property": property_id,
                "spot_label": "A1",
                "vehicle_type": "CAR",
                "length_cm": 500,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )
        self.assertEqual(space_resp.status_code, status.HTTP_201_CREATED)
        # Price is calculated automatically: (500*250*200)/1_000_000 * 2.00 = 50.00
        self.assertEqual(str(space_resp.data["price_per_hour"]), "50.00")
        space_id = space_resp.data["id"]

        # Future window: tomorrow for 2 hours (format with Z for clean URL query param)
        now = timezone.now()
        start_time = (now + datetime.timedelta(days=1)).replace(microsecond=0)
        end_time = start_time + datetime.timedelta(hours=2)
        start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 4. User B searches -> sees User A's space
        search_resp = self.client_b.get(
            f"/api/spaces/available/?start={start_str}&end={end_str}&city=Ahmedabad",
        )
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)
        found_ids = [s["id"] for s in search_resp.data["results"]]
        self.assertIn(space_id, found_ids)

        # 5. User B reserves User A's space for 2 hours -> total_price = 100.00 (2 hrs * 50.00)
        reserve_resp = self.client_b.post(
            "/api/reservations/",
            {
                "space": space_id,
                "start_time": start_str,
                "end_time": end_str,
            },
            format="json",
        )
        self.assertEqual(reserve_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(reserve_resp.data["total_price"]), "100.00")
        self.assertEqual(reserve_resp.data["status"], "CONFIRMED")
        reservation_id = reserve_resp.data["id"]

        # 6. User B searches again -> space is gone for that window
        search_after_reserve = self.client_b.get(
            f"/api/spaces/available/?start={start_str}&end={end_str}&city=Ahmedabad",
        )
        self.assertEqual(search_after_reserve.status_code, status.HTTP_200_OK)
        found_ids_after = [s["id"] for s in search_after_reserve.data["results"]]
        self.assertNotIn(space_id, found_ids_after)

        # 7. User B cancels the reservation
        cancel_resp = self.client_b.post(
            f"/api/reservations/{reservation_id}/cancel/",
        )
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_resp.data["status"], "CANCELLED")

        # 8. User B searches again -> space is back
        search_after_cancel = self.client_b.get(
            f"/api/spaces/available/?start={start_str}&end={end_str}&city=Ahmedabad",
        )
        self.assertEqual(search_after_cancel.status_code, status.HTTP_200_OK)
        found_ids_restored = [s["id"] for s in search_after_cancel.data["results"]]
        self.assertIn(space_id, found_ids_restored)

        # 9. Bonus: User A tries to reserve their own space -> gets 400 (cannot self-book)
        self_book_resp = self.client_a.post(
            "/api/reservations/",
            {
                "space": space_id,
                "start_time": start_str,
                "end_time": end_str,
            },
            format="json",
        )
        self.assertEqual(self_book_resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 10. Bonus: User A deletes their account (DELETE /api/auth/me/ -> 204)
        delete_resp = self.client_a.delete("/api/auth/me/")
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)

        # A's old token now returns 401
        me_resp = self.client_a.get("/api/auth/me/")
        self.assertEqual(me_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # User B's search no longer lists A's spaces (proves soft delete)
        search_after_delete = self.client_b.get(
            f"/api/spaces/available/?start={start_str}&end={end_str}&city=Ahmedabad",
        )
        self.assertEqual(search_after_delete.status_code, status.HTTP_200_OK)
        found_ids_deleted = [s["id"] for s in search_after_delete.data["results"]]
        self.assertNotIn(space_id, found_ids_deleted)
