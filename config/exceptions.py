"""
Custom exception handler and exception classes for Shared Parking System.
Ensures standard error response format across all endpoints (Section 3.3).
"""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class SlotUnavailableError(APIException):
    """
    Raised when attempting to reserve a time slot that is already booked (Rule 2).
    Returns HTTP 409 Conflict.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This time slot is already booked."
    default_code = "slot_unavailable"


def custom_exception_handler(exc, context):
    """
    Custom exception handler to normalize API error responses:
    - 400 Validation errors: wrapped in {"errors": {...}}
    - 401 / 403 / 404 / 409 errors: {"detail": "..."}
    """
    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            if isinstance(response.data, dict) and "errors" not in response.data:
                response.data = {"errors": response.data}
            elif isinstance(response.data, list):
                response.data = {"errors": {"non_field_errors": response.data}}

    return response
