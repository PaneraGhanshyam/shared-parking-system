from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

phone_validator = RegexValidator(r"^\+?\d{7,15}$", "Enter a valid phone number.")


class User(AbstractUser):
    email = models.EmailField("email address", unique=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    deleted_at = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at"])

    def __str__(self):
        return self.username
