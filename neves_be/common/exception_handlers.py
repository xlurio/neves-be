from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from neves_be.common.api import error_response

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.response import Response


logger = logging.getLogger(__name__)


def _build_error_log_extra(context: dict[str, Any]) -> dict[str, Any]:
    request: Request | Any | None = context.get("request")
    view = context.get("view")
    return {
        "request_method": getattr(request, "method", None),
        "request_path": getattr(request, "path", None),
        "view": view.__class__.__name__ if view is not None else None,
    }


def _mark_traceback_logged(context: dict[str, Any]) -> None:
    request = context.get("request")
    if request is not None:
        request.__dict__["_traceback_logged"] = True


def custom_exception_handler(
    exc: Exception | APIException,
    context: dict[str, Any],
) -> Response:
    response = exception_handler(exc, context)
    log_extra = _build_error_log_extra(context)

    if response is None:
        logger.exception("Unhandled API exception", extra=log_extra)
        _mark_traceback_logged(context)
        return error_response(
            "INTERNAL_ERROR",
            "Internal server error",
            "An unexpected error occurred.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            "API request ended with server error response",
            exc_info=(type(exc), exc, exc.__traceback__),
            extra={
                **log_extra,
                "status_code": response.status_code,
            },
        )
        _mark_traceback_logged(context)

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
