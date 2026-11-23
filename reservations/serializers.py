from rest_framework import serializers
from django.utils import timezone
from rest_framework import serializers

from spaces.models import Space
from spaces.serializers import SpaceSerializer

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
    space = serializers.PrimaryKeyRelatedField(
        queryset=Space.objects.active()
    )
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
        space = attrs["space"]

        # End time must be after start time
        if end_time <= start_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )

        # Users cannot reserve their own spaces
        request = self.context.get("request")

        if request and space.parking_property.owner_id == request.user.id:
            raise serializers.ValidationError(
                "You cannot reserve your own space."
            )

        return attrs
        
