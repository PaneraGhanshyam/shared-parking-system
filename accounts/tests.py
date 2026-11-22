from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_phone_number(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            phone_number="+919876543210",
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.phone_number, "+919876543210")
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deleted_at)

    def test_soft_delete(self):
        user = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="testpassword123",
        )
        self.assertTrue(user.is_active)
        self.assertIsNone(user.deleted_at)

        user.soft_delete()
        user.refresh_from_db()

        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)

    def test_email_uniqueness(self):
        User.objects.create_user(
            username="user1",
            email="unique@example.com",
            password="password1",
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email="unique@example.com",
                password="password2",
            )


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.me_url = "/api/auth/me/"

    def test_register_success(self):
        data = {
            "username": "john",
            "email": "john@example.com",
            "password": "securePass123",
            "phone_number": "+919876543210",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "john")
        self.assertEqual(response.data["email"], "john@example.com")
        self.assertEqual(response.data["phone_number"], "+919876543210")
        self.assertNotIn("password", response.data)

    def test_register_without_phone_number(self):
        data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "securePass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone_number"], "")

    def test_register_duplicate_username(self):
        self.client.post(
            self.register_url,
            {"username": "dupuser", "email": "dup1@example.com", "password": "securePass123"},
            format="json",
        )
        response = self.client.post(
            self.register_url,
            {"username": "dupuser", "email": "dup2@example.com", "password": "securePass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data.get("errors", response.data))

    def test_register_duplicate_email(self):
        self.client.post(
            self.register_url,
            {"username": "userone", "email": "shared@example.com", "password": "securePass123"},
            format="json",
        )
        response = self.client.post(
            self.register_url,
            {"username": "usertwo", "email": "shared@example.com", "password": "securePass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data.get("errors", response.data))

    def test_register_invalid_phone_number(self):
        data = {
            "username": "badphone",
            "email": "badphone@example.com",
            "password": "securePass123",
            "phone_number": "123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data.get("errors", response.data))

    def test_login_success(self):
        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="secretpassword",
        )
        data = {"username": "loginuser", "password": "secretpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], "loginuser")
        self.assertIn("user_id", response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="secretpassword",
        )
        data = {"username": "loginuser", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("detail"), "Invalid username or password.")

    def test_login_nonexistent_user(self):
        data = {"username": "nobody", "password": "somepassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get("detail"), "Invalid username or password.")

    def test_current_user_authenticated(self):
        user = User.objects.create_user(
            username="meuser",
            email="me@example.com",
            password="secretpassword",
            phone_number="+919876543210",
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "id": user.id,
                "username": "meuser",
                "email": "me@example.com",
                "phone_number": "+919876543210",
            },
        )

    def test_current_user_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("detail"), "Authentication credentials were not provided.")

    def test_soft_delete_and_lifecycle(self):
        user = User.objects.create_user(
            username="deluser",
            email="del@example.com",
            password="secretpassword",
        )
        token = Token.objects.create(user=user)
        token_key = token.key

        # 1. DELETE /api/auth/me/ returns 204
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_key}")
        delete_response = self.client.delete(self.me_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # 2. User record still exists in DB, is_active is False, deleted_at is set
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)

        # 3. Old token is deleted; using it returns 401
        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4. Login attempt with deleted user returns 400
        self.client.credentials()  # clear credentials
        login_response = self.client.post(
            self.login_url,
            {"username": "deluser", "password": "secretpassword"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(login_response.data.get("detail"), "Invalid username or password.")
