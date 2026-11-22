from rest_framework import serializers
from .models import ParkingProperty, Space

class ParkingPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingProperty
        fields = [
            "id",
            "title",
            "description",
            "address",
            "city",
            "state",
            "postal_code",
            "owner",
            "is_active",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "is_active",
            "deleted_at",
        ]

class SpaceSerializer(serializers.ModelSerializer):
    owner = serializers.IntegerField(
        source="parking_property.owner_id",
        read_only=True,
    )
    property_title = serializers.CharField(
        source="parking_property.title",
        read_only=True,
    )
    address = serializers.CharField(
        source="parking_property.address",
        read_only=True,
    )
    city = serializers.CharField(
        source="parking_property.city",
        read_only=True,
    )

    class Meta:
        model = Space
        fields = [
            "id",
            "parking_property",
            "owner",
            "property_title",
            "address",
            "city",
            "spot_label",
            "vehicle_type",
            "length_cm",
            "width_cm",
            "height_cm",
            "price_per_hour",
            "is_active",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "property_title",
            "address",
            "city",
            "price_per_hour",
            "is_active",
            "deleted_at",
        ]
        validators=[]

    def get_fields(self):
        fields = super().get_fields()

        # Property can be selected during creation,
        # but cannot be changed after creation.
        if self.instance is not None:
            fields["parking_property"].read_only = True

        return fields

    def validate_parking_property(self, value):
        request = self.context.get("request")

        if (
            not value.is_active
            or request is None
            or value.owner_id != request.user.id
        ):
            raise serializers.ValidationError(
                "You can only add spaces to your own properties."
            )

        return value

    def validate_length_cm(self, value):
        if not 50 <= value <= 2000:
            raise serializers.ValidationError(
                "Ensure this value is between 50 and 2000."
            )
        return value

    def validate_width_cm(self, value):
        if not 50 <= value <= 2000:
            raise serializers.ValidationError(
                "Ensure this value is between 50 and 2000."
            )
        return value

    def validate_height_cm(self, value):
        if not 50 <= value <= 2000:
            raise serializers.ValidationError(
                "Ensure this value is between 50 and 2000."
            )
        return value
   
    def validate(self, attrs):
        parking_property = attrs.get(
            "parking_property",
            getattr(self.instance, "parking_property", None),
        )
        spot_label = attrs.get(
            "spot_label",
            getattr(self.instance, "spot_label", None),
        )

        if parking_property and spot_label:
            duplicate_spaces = Space.objects.filter(
                parking_property=parking_property,
                spot_label=spot_label,
            )

            if self.instance:
                duplicate_spaces = duplicate_spaces.exclude(
                    pk=self.instance.pk
                )

            if duplicate_spaces.exists():
                raise serializers.ValidationError({
                    "spot_label": [
                        "This property already has a space with this label."
                    ]
                })

        return attrs
