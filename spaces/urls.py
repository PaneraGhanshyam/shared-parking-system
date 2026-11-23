from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, SpaceViewSet
from .views_search import AvailableSpaceView

router = DefaultRouter()
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"spaces", SpaceViewSet, basename="space")

urlpatterns = [
    path("spaces/available/", AvailableSpaceView.as_view(), name="available-spaces"),
] + router.urls
