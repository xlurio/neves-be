from http import HTTPStatus

import pytest
from django.utils.crypto import get_random_string

from tests.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_create_requires_credentials(client):
    response = client.post("/api/users", data={}, content_type="application/json")

    assert response.status_code == HTTPStatus.CONFLICT
    payload = response.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "title" in payload
    assert "details" in payload


def test_user_create_rejects_existing_username(client):
    user = UserFactory.create(username="duplicate-user")

    response = client.post(
        "/api/users",
        data={"username": user.username, "password": "secret123"},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.CONFLICT
    payload = response.json()
    assert payload["code"] == "USER_EXISTS"
    assert "title" in payload
    assert "details" in payload


def test_authenticate_requires_credentials(client):
    response = client.post(
        "/api/authenticate",
        data={},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    payload = response.json()
    assert payload["code"] == "INVALID_CREDENTIALS"
    assert "title" in payload
    assert "details" in payload


def test_authenticate_logs_user_in(client):
    password = get_random_string(length=24)
    user = UserFactory.create(username="auth-user")
    user.set_password(password)
    user.save(update_fields=["password"])

    response = client.post(
        "/api/authenticate",
        data={"username": user.username, "password": password},
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.NO_CONTENT


def test_logout_requires_authentication(client):
    response = client.post(
        "/api/logout",
        data={},
        content_type="application/json",
    )

    assert response.status_code in {
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
    }
    payload = response.json()
    assert payload["code"] == "AUTH_ERROR"
    assert "title" in payload
    assert "details" in payload


def test_logout_logs_user_out(client):
    password = get_random_string(length=24)
    user = UserFactory.create(username="logout-user")
    user.set_password(password)
    user.save(update_fields=["password"])

    login_response = client.post(
        "/api/authenticate",
        data={"username": user.username, "password": password},
        content_type="application/json",
    )
    assert login_response.status_code == HTTPStatus.NO_CONTENT

    protected_response = client.get("/api/stats/me")
    assert protected_response.status_code == HTTPStatus.OK

    logout_response = client.post(
        "/api/logout",
        data={},
        content_type="application/json",
    )
    assert logout_response.status_code == HTTPStatus.NO_CONTENT

    logged_out_response = client.get("/api/stats/me")
    assert logged_out_response.status_code in {
        HTTPStatus.UNAUTHORIZED,
        HTTPStatus.FORBIDDEN,
    }
    payload = logged_out_response.json()
    assert payload["code"] == "AUTH_ERROR"
