from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from neves_be.common.api import error_response

if TYPE_CHECKING:
    from rest_framework.response import Response


def custom_exception_handler(exc, context) -> Response:
    response = exception_handler(exc, context)

    if response is None:
        return error_response(
            "INTERNAL_ERROR",
            "Internal server error",
            "An unexpected error occurred.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, Http404):
        return error_response(
            "NOT_FOUND",
            "Resource not found",
            "The requested resource does not exist.",
            http_status=response.status_code,
        )

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return error_response(
            "AUTH_ERROR",
            "Authentication failed",
            str(exc.detail),
            http_status=response.status_code,
        )

    if isinstance(exc, PermissionDenied):
        return error_response(
            "FORBIDDEN",
            "Forbidden",
            str(exc.detail),
            http_status=response.status_code,
        )

    if isinstance(exc, ValidationError):
        return error_response(
            "VALIDATION_ERROR",
            "Validation failed",
            "The request payload is invalid.",
            http_status=response.status_code,
            payload={"errors": response.data},
        )

    return error_response(
        "REQUEST_ERROR",
        "Request failed",
        str(getattr(exc, "detail", "The request could not be processed.")),
        http_status=response.status_code,
        payload={"errors": response.data},
    )
