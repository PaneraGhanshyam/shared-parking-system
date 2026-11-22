from rest_framework.routers import DefaultRouter

from .views import PropertyViewSet, SpaceViewSet

router = DefaultRouter()
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"spaces", SpaceViewSet, basename="space")

urlpatterns = router.urls
