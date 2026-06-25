from http import HTTPStatus

import pytest

pytestmark = pytest.mark.django_db


def test_radicals_sessions_requires_authentication(client):
    response = client.get("/api/radicals/sessions")
    assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
