from __future__ import annotations

import abc
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
from neves_be.common.exceptions import NevesBackEndError

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


class ExceptionHandler[T: Exception](abc.ABC):
    EXCEPTION_TYPE: type[T] | tuple[type[T], ...]

    def does_handle_exception(self, exc: T):
        return isinstance(exc, self.EXCEPTION_TYPE)

    @abc.abstractmethod
    def handle(self, exc: T, response: Response) -> Response:
        raise NotImplementedError


class NotFoundHandler(ExceptionHandler[Http404]):
    EXCEPTION_TYPE = Http404

    def handle(self, exc: Http404, response: Response) -> Response:
        del exc

        return error_response(
            "NOT_FOUND",
            "Resource not found",
            "The requested resource does not exist.",
            http_status=response.status_code,
        )


class AuthFailHandler(ExceptionHandler[NotAuthenticated | AuthenticationFailed]):
    EXCEPTION_TYPE = (NotAuthenticated, AuthenticationFailed)

    def handle(
        self,
        exc: NotAuthenticated | AuthenticationFailed,
        response: Response,
    ) -> Response:
        return error_response(
            "AUTH_ERROR",
            "Authentication failed",
            str(exc.detail),
            http_status=response.status_code,
        )


class ForbiddenHandler(ExceptionHandler[PermissionDenied]):
    EXCEPTION_TYPE = PermissionDenied

    def handle(
        self,
        exc: PermissionDenied,
        response: Response,
    ) -> Response:
        return error_response(
            "FORBIDDEN",
            "Forbidden",
            str(exc.detail),
            http_status=response.status_code,
        )


class ValidationHandler(ExceptionHandler[ValidationError]):
    EXCEPTION_TYPE = ValidationError

    def handle(
        self,
        exc: ValidationError,
        response: Response,
    ) -> Response:
        del exc

        return error_response(
            "VALIDATION_ERROR",
            "Validation failed",
            "The request payload is invalid.",
            http_status=response.status_code,
            payload={"errors": response.data},
        )


class NevesBackEndHandler(ExceptionHandler[NevesBackEndError]):
    EXCEPTION_TYPE = NevesBackEndError

    def handle(
        self,
        exc: NevesBackEndError,
        response: Response,
    ) -> Response:
        del response

        return error_response(
            exc.code,
            exc.title,
            exc.details,
            http_status=exc.http_status,
            payload=exc.payload,
        )


ExceptionType = type[Exception] | tuple[type[Exception], ...]


EXCEPTION_HANDLERS: set[type[ExceptionHandler]] = {
    NotFoundHandler,
    AuthFailHandler,
    ForbiddenHandler,
    ValidationHandler,
    NevesBackEndHandler,
}


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

    for handler_cls in EXCEPTION_HANDLERS:
        handler = handler_cls()

        if handler.does_handle_exception(exc):
            return handler.handle(exc, response)

    return error_response(
        "REQUEST_ERROR",
        "Request failed",
        str(getattr(exc, "detail", "The request could not be processed.")),
        http_status=response.status_code,
        payload={"errors": response.data},
    )
