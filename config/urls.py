
"""
URL configuration for Shared Parking System.
Created by M1. Each team member registers their app's API routes here.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import OpenApiExample, extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField(default="ok")


@extend_schema(
    summary="Health check",
    description="Public health check endpoint returning API service status.",
    responses={200: HealthCheckResponseSerializer},
    examples=[
        OpenApiExample(
            "Health Check Response",
            value={"status": "ok"},
            response_only=True,
        )
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    GET /api/health/
    Public health check endpoint (Section 3.4).
    """
    return Response({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health_check"),
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[AllowAny]), name="swagger-ui"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("spaces.urls")),
    path("api/reservations/", include("reservations.urls")),
]
