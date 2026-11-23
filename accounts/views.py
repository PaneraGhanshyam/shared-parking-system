from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="DRF Auth Token")
    user_id = serializers.IntegerField(help_text="User Primary Key")
    username = serializers.CharField(help_text="Username")


@extend_schema(
    summary="Create Account (Register)",
    description="Register a new user account. Every user can list spaces and make reservations.",
    request=RegisterSerializer,
    responses={201: UserSerializer},
    examples=[
        OpenApiExample(
            "Register Request Example",
            value={
                "username": "ravi",
                "email": "ravi@example.com",
                "password": "securePass123",
                "phone_number": "+919876543210",
            },
            request_only=True,
        ),
        OpenApiExample(
            "Register Response Example",
            value={
                "id": 1,
                "username": "ravi",
                "email": "ravi@example.com",
                "phone_number": "+919876543210",
            },
            response_only=True,
        ),
    ],
)
class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Registers a new user and returns user details.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Validates credentials and returns auth token, user_id and username.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get Token (Login)",
        description="Authenticate with username and password to retrieve DRF auth token.",
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        examples=[
            OpenApiExample(
                "Login Request Example",
                value={
                    "username": "ravi",
                    "password": "securePass123",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Login Response Example",
                value={
                    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
                    "user_id": 1,
                    "username": "ravi",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    GET /api/auth/me/
    Returns authenticated user's profile details.

    DELETE /api/auth/me/
    Soft-deletes the user account and deletes auth token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current User Profile",
        description="Retrieve profile details for the currently authenticated user.",
        responses={200: UserSerializer},
    )
    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Delete My Account (Soft Delete)",
        description="Deactivate the authenticated user's account and revoke active auth token.",
        responses={204: None},
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        Token.objects.filter(user=user).delete()
        user.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
