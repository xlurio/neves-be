from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import TypedDict

from rest_framework.response import Response

if TYPE_CHECKING:
    from rest_framework.request import Request


type ErrorCode = Literal[
    "INTERNAL_ERROR",
    "NOT_FOUND",
    "AUTH_ERROR",
    "FORBIDDEN",
    "VALIDATION_ERROR",
    "REQUEST_ERROR",
    "INVALID_CREDENTIALS",
    "USER_EXISTS",
    "NOT_ENOUGH_RADICALS",
    "INVALID_QUESTION",
    "INVALID_ANSWER",
    "QUESTION_MISSED",
    "UNFINISHED_ASSESSMENT",
]


class ErrorResponsePayload(TypedDict):
    code: ErrorCode
    title: str
    details: str
    payload: dict[str, Any]


def load_request_data(request: Request) -> dict[str, Any]:
    if isinstance(request.data, dict):
        return request.data
    try:
        return dict(request.data)
    except TypeError, ValueError, JSONDecodeError:
        return {}


def error_response(
    code: ErrorCode,
    title: str,
    details: str,
    *,
    http_status: int,
    payload: dict[str, Any] | None = None,
) -> Response:
    response_payload: ErrorResponsePayload = {
        "code": code,
        "title": title,
        "details": details,
        "payload": {},
    }
    if payload is not None:
        response_payload["payload"] = payload
    return Response(response_payload, status=http_status)
