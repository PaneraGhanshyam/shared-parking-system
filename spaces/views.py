from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ParkingProperty, Space
from .permissions import IsOwnerOrReadOnly
from .serializers import ParkingPropertySerializer, SpaceSerializer


@extend_schema_view(
    list=extend_schema(
        summary="My Properties",
        description="List all active properties owned by the authenticated user.",
    ),
    create=extend_schema(
        summary="Register a Property",
        description="Register a new parking property. Owner is set automatically from the auth token.",
        examples=[
            OpenApiExample(
                "Property Creation Example",
                value={
                    "title": "Ravi's Home",
                    "description": "Gated society, ground-floor parking",
                    "address": "12 Lake View Society",
                    "city": "Ahmedabad",
                    "state": "Gujarat",
                    "postal_code": "380015",
                },
                request_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Property Detail",
        description="Retrieve details of a specific property owned by the authenticated user.",
    ),
    partial_update=extend_schema(
        summary="Update a Property",
        description="Partially update property details (owner only).",
        examples=[
            OpenApiExample(
                "Property Partial Update Example",
                value={
                    "title": "Ravi's Home (Ground Floor)",
                    "description": "Updated society instructions",
                },
                request_only=True,
            )
        ],
    ),
    destroy=extend_schema(
        summary="Deactivate Property (Soft Delete)",
        description="Soft delete a property and all its associated parking spaces (owner only).",
    ),
)
class PropertyViewSet(viewsets.ModelViewSet):
    queryset = ParkingProperty.objects.all()
    serializer_class = ParkingPropertySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return ParkingProperty.objects.filter(
            owner=self.request.user,
            is_active=True,
            owner__is_active=True,
        ).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema_view(
    list=extend_schema(
        summary="List Active Spaces",
        description="List all active parking spaces across all active properties.",
    ),
    create=extend_schema(
        summary="Register a Space in a Property",
        description="Add a new parking space to an owned property. Hourly fee is calculated automatically.",
        examples=[
            OpenApiExample(
                "Car Space Example",
                value={
                    "parking_property": 1,
                    "spot_label": "A1",
                    "vehicle_type": "CAR",
                    "length_cm": 500,
                    "width_cm": 250,
                    "height_cm": 200,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Bike Space Example",
                value={
                    "parking_property": 1,
                    "spot_label": "B1",
                    "vehicle_type": "BIKE",
                    "length_cm": 200,
                    "width_cm": 100,
                    "height_cm": 150,
                },
                request_only=True,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Space Detail",
        description="Retrieve details of a specific active parking space.",
    ),
    partial_update=extend_schema(
        summary="Update a Space",
        description="Partially update space dimensions or spot label. Dimensions recalculate hourly rate.",
        examples=[
            OpenApiExample(
                "Dimension Update Example",
                value={
                    "length_cm": 550,
                },
                request_only=True,
            )
        ],
    ),
    destroy=extend_schema(
        summary="Deactivate Space (Soft Delete)",
        description="Soft delete a parking space (owner only).",
    ),
)
class SpaceViewSet(viewsets.ModelViewSet):
    queryset = Space.objects.all()
    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Space.objects.active().order_by("id")

    def perform_destroy(self, instance):
        instance.soft_delete()
