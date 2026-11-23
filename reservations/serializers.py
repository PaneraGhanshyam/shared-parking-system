
from django.utils import timezone
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


class CreateReservationSerializer(serializers.Serializer):
    space = serializers.IntegerField(min_value=1)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Start time must be in the future."
            )
        return value

    def validate(self, attrs):
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]

        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )

        return attrs
