from __future__ import annotations

import logging
from http import HTTPStatus

import pytest
from django.http import HttpResponse
from django.test import override_settings
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from neves_be.common.middleware import ServerErrorTracebackLoggingMiddleware
from tests.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def _boom_view(_request):
    msg = "boom"
    raise RuntimeError(msg)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def _explicit_500_view(_request):
    return HttpResponse(status=500)


urlpatterns = [
    path("api/test-boom", _boom_view),
]


@override_settings(ROOT_URLCONF=__name__)
def test_unhandled_api_exception_logs_traceback(client, caplog):
    user = UserFactory.create()
    client.force_login(user)

    with caplog.at_level(logging.ERROR):
        response = client.get("/api/test-boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    matching = [
        record
        for record in caplog.records
        if record.name == "neves_be.common.exception_handlers"
        and "Unhandled API exception" in record.message
    ]
    assert matching
    assert matching[0].exc_info is not None


def test_middleware_logs_traceback_stack_for_500_response(rf, caplog):
    request = rf.get("/test-500")
    middleware = ServerErrorTracebackLoggingMiddleware(
        lambda _request: HttpResponse(status=500),
    )

    with caplog.at_level(logging.ERROR):
        response = middleware(request)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    matching = [
        record
        for record in caplog.records
        if record.name == "neves_be.common.middleware"
        and "HTTP 5xx response generated without captured exception traceback"
        in record.message
    ]
    assert matching
    assert matching[0].stack_info is not None


def test_middleware_does_not_log_twice_when_traceback_already_logged(rf, caplog):
    request = rf.get("/test-500")
    request.__dict__["_traceback_logged"] = True
    middleware = ServerErrorTracebackLoggingMiddleware(
        lambda _request: HttpResponse(status=500),
    )

    with caplog.at_level(logging.ERROR):
        response = middleware(request)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert not [
        record
        for record in caplog.records
        if record.name == "neves_be.common.middleware"
    ]
