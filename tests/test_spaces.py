
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from spaces.models import ParkingProperty, Space

User = get_user_model()


class SpaceRegistrationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="testpass123",
        )

        self.client.force_authenticate(user=self.owner)

        self.property = ParkingProperty.objects.create(
            title="My Parking",
            description="Test parking property",
            address="123 Main Road",
            city="Junagadh",
            state="Gujarat",
            postal_code="362001",
            owner=self.owner,
        )

    def test_owner_can_create_property(self):
        response = self.client.post(
            "/api/properties/",
            {
                "title": "New Parking",
                "description": "Another property",
                "address": "456 Main Road",
                "city": "Junagadh",
                "state": "Gujarat",
                "postal_code": "362001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            ParkingProperty.objects.filter(owner=self.owner).count(),
            2,
        )

    def test_owner_can_create_space(self):
        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A1",
                "vehicle_type": "CAR",
                "length_cm": 500,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Space.objects.filter(
                parking_property=self.property,
                spot_label="A1",
            ).exists()
        )

    def test_space_price_is_calculated_automatically(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A2",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        self.assertEqual(
            space.price_per_hour,
            Decimal("50.00"),
        )

    # Property privacy tests

    def test_other_user_cannot_retrieve_property(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            f"/api/properties/{self.property.id}/"
        )

        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_update_property(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/properties/{self.property.id}/",
            {"title": "Changed title"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_delete_property(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/properties/{self.property.id}/"
        )

        self.assertEqual(response.status_code, 404)

        self.property.refresh_from_db()
        self.assertTrue(self.property.is_active)

    def test_user_can_only_see_own_properties(self):
        ParkingProperty.objects.create(
            title="Other User Parking",
            description="Private property",
            address="789 Main Road",
            city="Junagadh",
            state="Gujarat",
            postal_code="362001",
            owner=self.other_user,
        )

        response = self.client.get("/api/properties/")

        self.assertEqual(response.status_code, 200)

        property_titles = [
            item["title"] for item in response.data["results"]
        ]

        self.assertIn("My Parking", property_titles)
        self.assertNotIn("Other User Parking", property_titles)

    # Property soft-delete tests

    def test_property_delete_is_soft_delete(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A3",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        response = self.client.delete(
            f"/api/properties/{self.property.id}/"
        )

        self.assertEqual(response.status_code, 204)

        self.property.refresh_from_db()
        self.assertFalse(self.property.is_active)
        self.assertIsNotNone(self.property.deleted_at)

        space.refresh_from_db()
        self.assertFalse(space.is_active)
        self.assertIsNotNone(space.deleted_at)

    # Space public-listing and ownership tests

    def test_other_user_can_view_space(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A12",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            f"/api/spaces/{space.id}/"
        )

        self.assertEqual(response.status_code, 200)

    def test_other_user_can_see_space_in_list(self):
        Space.objects.create(
            parking_property=self.property,
            spot_label="A14",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.get("/api/spaces/")

        self.assertEqual(response.status_code, 200)

        spot_labels = [
            item["spot_label"] for item in response.data["results"]
        ]

        self.assertIn("A14", spot_labels)

    def test_other_user_cannot_update_space(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A13",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            f"/api/spaces/{space.id}/",
            {"spot_label": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        space.refresh_from_db()
        self.assertEqual(space.spot_label, "A13")

    def test_other_user_cannot_delete_space(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A15",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            f"/api/spaces/{space.id}/"
        )

        self.assertEqual(response.status_code, 403)

        space.refresh_from_db()
        self.assertTrue(space.is_active)

    # Space validation tests

    def test_space_rejects_dimensions_below_minimum(self):
        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A4",
                "vehicle_type": "CAR",
                "length_cm": 49,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("length_cm", response.data["errors"])

    def test_space_rejects_dimensions_above_maximum(self):
        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A5",
                "vehicle_type": "CAR",
                "length_cm": 2001,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("length_cm", response.data["errors"])

    def test_duplicate_space_label_is_rejected(self):
        Space.objects.create(
            parking_property=self.property,
            spot_label="A6",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A6",
                "vehicle_type": "BIKE",
                "length_cm": 200,
                "width_cm": 100,
                "height_cm": 100,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("spot_label", response.data["errors"])

    def test_user_cannot_create_space_on_another_users_property(self):
        other_property = ParkingProperty.objects.create(
            title="Other Parking",
            description="Another user's parking",
            address="789 Main Road",
            city="Junagadh",
            state="Gujarat",
            postal_code="362001",
            owner=self.other_user,
        )

        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": other_property.id,
                "spot_label": "B1",
                "vehicle_type": "CAR",
                "length_cm": 500,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("parking_property", response.data["errors"])

    def test_user_cannot_create_space_on_inactive_property(self):
        self.property.soft_delete()

        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A7",
                "vehicle_type": "CAR",
                "length_cm": 500,
                "width_cm": 250,
                "height_cm": 200,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("parking_property", response.data["errors"])

    def test_space_property_cannot_be_changed_after_creation(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A8",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        another_property = ParkingProperty.objects.create(
            title="Second Parking",
            description="Another property",
            address="456 Main Road",
            city="Junagadh",
            state="Gujarat",
            postal_code="362001",
            owner=self.owner,
        )

        response = self.client.patch(
            f"/api/spaces/{space.id}/",
            {"parking_property": another_property.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        space.refresh_from_db()
        self.assertEqual(space.parking_property, self.property)

    def test_client_cannot_set_space_price(self):
        response = self.client.post(
            "/api/spaces/",
            {
                "parking_property": self.property.id,
                "spot_label": "A9",
                "vehicle_type": "CAR",
                "length_cm": 500,
                "width_cm": 250,
                "height_cm": 200,
                "price_per_hour": "1.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Decimal(response.data["price_per_hour"]),
            Decimal("50.00"),
        )

    def test_updating_dimensions_recalculates_price(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A10",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        response = self.client.patch(
            f"/api/spaces/{space.id}/",
            {"length_cm": 600},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        space.refresh_from_db()
        self.assertEqual(
            space.price_per_hour,
            Decimal("60.00"),
        )

    def test_inactive_space_cannot_be_retrieved(self):
        space = Space.objects.create(
            parking_property=self.property,
            spot_label="A11",
            vehicle_type="CAR",
            length_cm=500,
            width_cm=250,
            height_cm=200,
        )

        space.soft_delete()

        response = self.client.get(
            f"/api/spaces/{space.id}/"
        )

        self.assertEqual(response.status_code, 404)
