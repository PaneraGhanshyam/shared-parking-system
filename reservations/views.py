from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservation
from .serializers import (
    CreateReservationSerializer,
    ReservationSerializer,
)
from .services import cancel_reservation, create_reservation


@extend_schema_view(
    list=extend_schema(
        summary="My Reservations",
        description="List all reservations booked by the authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Reservation Detail",
        description="Retrieve full details for a single reservation owned by the user.",
    ),
    create=extend_schema(
        summary="Reserve a Space",
        description="Reserve an active parking space for a future time window. Double booking is prevented.",
        request=CreateReservationSerializer,
        responses={201: ReservationSerializer},
        examples=[
            OpenApiExample(
                "Create Reservation Example",
                value={
                    "space": 1,
                    "start_time": "2026-11-25T09:00:00Z",
                    "end_time": "2026-11-25T11:00:00Z",
                },
                request_only=True,
            )
        ],
    ),
    cancel=extend_schema(
        summary="Cancel a Reservation",
        description="Cancel a confirmed upcoming reservation and immediately free the parking slot.",
        request=None,
        responses={200: ReservationSerializer},
    ),
)
class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Reservation.objects.filter(user=self.request.user)
            .select_related(
                "user",
                "space__parking_property",
            )
            .order_by("-created_at", "-id")
        )

    def create(self, request, *args, **kwargs):
        input_serializer = CreateReservationSerializer(
            data=request.data,
            context={"request": request},
        )
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        reservation = create_reservation(
            user=request.user,
            space=validated_data["space"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
        )

        output_serializer = ReservationSerializer(
            reservation,
            context=self.get_serializer_context(),
        )

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        reservation = cancel_reservation(
            user=request.user,
            reservation_id=pk,
        )

        serializer = self.get_serializer(reservation)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
