from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

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
