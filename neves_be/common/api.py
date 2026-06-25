from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING
from typing import Any
from typing import TypedDict

from rest_framework.response import Response

if TYPE_CHECKING:
    from rest_framework.request import Request


class ErrorResponsePayload(TypedDict):
    code: str
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
    code: str,
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
