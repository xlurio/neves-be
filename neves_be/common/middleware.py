from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rest_framework import status

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest
    from django.http import HttpResponseBase


logger = logging.getLogger(__name__)


class ServerErrorTracebackLoggingMiddleware:
    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponseBase],
    ) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        response = self.get_response(request)

        if (
            response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR
            and not getattr(
                request,
                "_traceback_logged",
                False,
            )
        ):
            logger.error(
                "HTTP 5xx response generated without captured exception traceback",
                extra={
                    "request_method": request.method,
                    "request_path": request.path,
                    "status_code": response.status_code,
                },
                stack_info=True,
            )

        return response
