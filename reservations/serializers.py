from rest_framework import serializers

from spaces.serializers import SpaceSerializer

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    space = SpaceSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "user",
            "space",
            "start_time",
            "end_time",
            "total_price",
            "status",
            "created_at",
            "cancelled_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "space",
            "start_time",
            "end_time",
            "total_price",
            "status",
            "created_at",
            "cancelled_at",
        ]
