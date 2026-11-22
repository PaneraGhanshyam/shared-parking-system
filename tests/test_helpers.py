from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from tests.helpers import authenticated_client, create_property, create_space, create_user

User = get_user_model()


class SharedTestHelpersTests(TestCase):
    def test_create_user_default_fields(self):
        user = create_user()
        self.assertTrue(user.username.startswith("user_"))
        self.assertTrue(user.email.endswith("@example.com"))
        self.assertEqual(user.phone_number, "+919876543210")
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("testpassword123"))

    def test_create_user_custom_fields(self):
        user = create_user(
            username="customuser",
            email="custom@example.com",
            password="custompassword",
            phone_number="+911234567890",
        )
        self.assertEqual(user.username, "customuser")
        self.assertEqual(user.email, "custom@example.com")
        self.assertEqual(user.phone_number, "+911234567890")
        self.assertTrue(user.check_password("custompassword"))

    def test_authenticated_client_with_new_user(self):
        client = authenticated_client()
        self.assertIsNotNone(client.user)
        response = client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_client_with_existing_user(self):
        user = create_user(username="existinguser")
        client = authenticated_client(user=user)
        self.assertEqual(client.user, user)
