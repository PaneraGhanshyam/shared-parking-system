
from rest_framework import views, serializers
from rest_framework.permissions import IsAuthenticated
from reservations.models import Reservation
from .models import Space
from rest_framework.pagination import PageNumberPagination
from spaces.serializers import SpaceSerializer

class AvailabilitySearchQuerySerializer(serializers.Serializer):
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    vehicle_type = serializers.ChoiceField(choices=Space.VehicleType.choices , required=False)
    city = serializers.CharField(required=False,allow_blank=False)
    max_price = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0,
        required=False
    )

    def validate(self,attrs):
        # validation for start time and end time
        if attrs["end"] <= attrs["start"]:
            raise serializers.ValidationError({"end" : ["end must be after start."]})

        return attrs

class AvailableSpaceView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        serializer = AvailabilitySearchQuerySerializer(data=request.query_params)

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        booked_space_ids = Reservation.objects.confirmed().overlapping(data["start"], data["end"]).values_list("space_id", flat=True)

        queryset = Space.objects.active().exclude(id__in=booked_space_ids)

        if "city" in data:
            queryset = queryset.filter(parking_property__city__iexact=data["city"])

        if "vehicle_type" in data:
            queryset = queryset.filter(vehicle_type=data["vehicle_type"])

        if "max_price" in data:
            queryset = queryset.filter(price_per_hour__lte=data["max_price"])

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset.order_by("id"), request)
        serializer = SpaceSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
