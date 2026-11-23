
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Reservation
from .serializers import ReservationSerializer


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
        """
        Extension slot for M6: Reserve a space.
        Temporary placeholder returning HTTP 501 NOT IMPLEMENTED.
        """
        return Response(
            {"detail": "Reservation creation will be implemented in M6."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
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
