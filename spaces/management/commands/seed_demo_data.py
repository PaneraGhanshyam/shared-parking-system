from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from spaces.models import ParkingProperty, Space

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data with multiple users, properties, and spaces of mixed vehicle types."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        demo_users = [
            {
                "username": "ravi",
                "email": "ravi@example.com",
                "phone_number": "+919876543210",
                "password": "securePass123",
                "properties": [
                    {
                        "title": "Ravi's Home",
                        "description": "Gated society, ground-floor parking",
                        "address": "12 Lake View Society",
                        "city": "Ahmedabad",
                        "state": "Gujarat",
                        "postal_code": "380015",
                        "spaces": [
                            {
                                "spot_label": "A1",
                                "vehicle_type": Space.VehicleType.CAR,
                                "length_cm": 500,
                                "width_cm": 250,
                                "height_cm": 200,
                            },
                            {
                                "spot_label": "B1",
                                "vehicle_type": Space.VehicleType.BIKE,
                                "length_cm": 200,
                                "width_cm": 100,
                                "height_cm": 150,
                            },
                        ],
                    }
                ],
            },
            {
                "username": "priya",
                "email": "priya@example.com",
                "phone_number": "+919876543211",
                "password": "securePass123",
                "properties": [
                    {
                        "title": "Priya's Office",
                        "description": "Commercial parking complex with 24/7 security",
                        "address": "456 Park Ave",
                        "city": "Ahmedabad",
                        "state": "Gujarat",
                        "postal_code": "380001",
                        "spaces": [
                            {
                                "spot_label": "C1",
                                "vehicle_type": Space.VehicleType.CAR,
                                "length_cm": 450,
                                "width_cm": 200,
                                "height_cm": 180,
                            },
                            {
                                "spot_label": "T1",
                                "vehicle_type": Space.VehicleType.TRUCK,
                                "length_cm": 1000,
                                "width_cm": 300,
                                "height_cm": 400,
                            },
                        ],
                    }
                ],
            },
            {
                "username": "rahul",
                "email": "rahul@example.com",
                "phone_number": "+919876543212",
                "password": "securePass123",
                "properties": [
                    {
                        "title": "Rahul's Commercial Garage",
                        "description": "Covered garage suitable for all vehicle sizes",
                        "address": "78 Ring Road",
                        "city": "Surat",
                        "state": "Gujarat",
                        "postal_code": "395001",
                        "spaces": [
                            {
                                "spot_label": "B2",
                                "vehicle_type": Space.VehicleType.BIKE,
                                "length_cm": 200,
                                "width_cm": 100,
                                "height_cm": 150,
                            },
                            {
                                "spot_label": "C2",
                                "vehicle_type": Space.VehicleType.CAR,
                                "length_cm": 550,
                                "width_cm": 280,
                                "height_cm": 220,
                            },
                            {
                                "spot_label": "T2",
                                "vehicle_type": Space.VehicleType.TRUCK,
                                "length_cm": 1000,
                                "width_cm": 300,
                                "height_cm": 400,
                            },
                        ],
                    }
                ],
            },
        ]

        total_users = 0
        total_properties = 0
        total_spaces = 0

        for user_data in demo_users:
            props = user_data.pop("properties")
            username = user_data.pop("username")
            password = user_data.pop("password")
            user = User.objects.filter(username=username).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    **user_data,
                )
                total_users += 1
                self.stdout.write(f"  Created user: {username} ({user.email})")
            else:
                self.stdout.write(f"  User already exists: {username}")

            for prop_data in props:
                spaces_data = prop_data.pop("spaces")
                title = prop_data.pop("title")
                prop = ParkingProperty.objects.filter(owner=user, title=title).first()
                if not prop:
                    prop = ParkingProperty.objects.create(
                        owner=user,
                        title=title,
                        **prop_data,
                    )
                    total_properties += 1
                    self.stdout.write(f"    Created property: {title} ({prop.city})")
                else:
                    self.stdout.write(f"    Property already exists: {title}")

                for space_data in spaces_data:
                    spot_label = space_data.pop("spot_label")
                    space = Space.objects.filter(
                        parking_property=prop,
                        spot_label=spot_label,
                    ).first()
                    if not space:
                        space = Space.objects.create(
                            parking_property=prop,
                            spot_label=spot_label,
                            **space_data,
                        )
                        total_spaces += 1
                        self.stdout.write(
                            f"      Created space: {spot_label} [{space.vehicle_type}] "
                            f"- {space.length_cm}x{space.width_cm}x{space.height_cm}cm "
                            f"(₹{space.price_per_hour}/hr)"
                        )
                    else:
                        self.stdout.write(f"      Space already exists: {spot_label}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded demo data! "
                f"({total_users} users, {total_properties} properties, {total_spaces} spaces)"
            )
        )
