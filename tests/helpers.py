import uuid
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


def create_user(
    username=None,
    email=None,
    password="testpassword123",
    phone_number="+919876543210",
    **kwargs,
):
    """Create and return a user using the custom User model."""
    User = get_user_model()
    if username is None:
        username = f"user_{uuid.uuid4().hex[:8]}"
    if email is None:
        email = f"{username}@example.com"
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        phone_number=phone_number,
        **kwargs,
    )


def create_property(
    owner=None,
    title="Test Property",
    city="Ahmedabad",
    address="123 Test St",
    **kwargs,
):
    """Create and return a ParkingProperty. Builds an owner if none given."""
    if owner is None:
        owner = create_user()
    ParkingProperty = apps.get_model("spaces", "ParkingProperty")
    return ParkingProperty.objects.create(
        owner=owner,
        title=title,
        city=city,
        address=address,
        **kwargs,
    )


def create_space(
    parking_property=None,
    vehicle_type="CAR",
    length_cm=500,
    width_cm=250,
    height_cm=200,
    spot_label=None,
    **kwargs,
):
    """Create and return a Space.

    - If no property is given, automatically build one.
    - Never set price manually; let the dimensions calculate it on save.
    """
    if parking_property is None:
        parking_property = create_property()
    if spot_label is None:
        spot_label = f"S-{uuid.uuid4().hex[:4]}"
    Space = apps.get_model("spaces", "Space")
    # Never set price manually; let the dimensions calculate it
    kwargs.pop("price_per_hour", None)
    return Space.objects.create(
        parking_property=parking_property,
        spot_label=spot_label,
        vehicle_type=vehicle_type,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        **kwargs,
    )


def authenticated_client(user=None):
    """Return a DRF APIClient with the user's Token pre-attached in authorization headers."""
    if user is None:
        user = create_user()
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    client.user = user
    return client
