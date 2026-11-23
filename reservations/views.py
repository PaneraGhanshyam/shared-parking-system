
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservation
from .serializers import (
    ReservationSerializer,
    CreateReservationSerializer,
)
from .services import create_reservation


class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
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
        """
        Extension slot for M7: Cancel reservation.
        Temporary placeholder returning HTTP 501 NOT IMPLEMENTED.
        """
        return Response(
            {"detail": "Reservation cancellation will be implemented in M7."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
