from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import ParkingProperty, Space
from .permissions import IsOwnerOrReadOnly
from .serializers import ParkingPropertySerializer, SpaceSerializer


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = ParkingPropertySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return ParkingProperty.objects.filter(
            owner=self.request.user,
            is_active=True,
            owner__is_active=True,
        ).order_by("id")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()
        
class SpaceViewSet(viewsets.ModelViewSet):
    serializer_class = SpaceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Space.objects.active().order_by("id")

    def perform_destroy(self, instance):
        instance.soft_delete()