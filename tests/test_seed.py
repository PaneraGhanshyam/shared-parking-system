from django.core.management import call_command
from django.test import TestCase
from spaces.models import ParkingProperty, Space
from django.contrib.auth import get_user_model

User = get_user_model()


class SeedDemoDataCommandTests(TestCase):
    def test_seed_demo_data_command(self):
        call_command("seed_demo_data")

        # Verify users created
        self.assertTrue(User.objects.filter(username="ravi").exists())
        self.assertTrue(User.objects.filter(username="priya").exists())
        self.assertTrue(User.objects.filter(username="rahul").exists())

        # Verify properties created
        self.assertTrue(ParkingProperty.objects.filter(title="Ravi's Home").exists())
        self.assertTrue(ParkingProperty.objects.filter(title="Priya's Office").exists())

        # Verify spaces of mixed vehicle types created
        self.assertTrue(Space.objects.filter(vehicle_type=Space.VehicleType.BIKE).exists())
        self.assertTrue(Space.objects.filter(vehicle_type=Space.VehicleType.CAR).exists())
        self.assertTrue(Space.objects.filter(vehicle_type=Space.VehicleType.TRUCK).exists())

        # Verify automatic pricing calculation on spaces
        car_space = Space.objects.get(parking_property__title="Ravi's Home", spot_label="A1")
        self.assertEqual(float(car_space.price_per_hour), 50.00)

        # Idempotence: calling again does not duplicate
        call_command("seed_demo_data")
        self.assertEqual(User.objects.filter(username="ravi").count(), 1)
