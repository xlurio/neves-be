from http import HTTPStatus

import pytest

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical
from neves_be.radicals.models import Radical
from tests.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def seed_radical(idx: int) -> Radical:
    return Radical.objects.create(
        id=f"r{idx}",
        pinyin=f"pin{idx}",
        meaning=f"meaning-{idx}",
        pronounce=f"/audio-cmn/18k-abr/syllabs/pin{idx}.mp3",
    )


def test_radicals_sessions_requires_authentication(client):
    response = client.get("/api/radicals/sessions")
    assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}
    payload = response.json()
    assert payload["code"] == "AUTH_ERROR"
    assert "title" in payload
    assert "details" in payload


def test_radicals_sessions_returns_empty_page_without_creating_session(client):
    user = UserFactory.create()
    client.force_login(user)

    response = client.get("/api/radicals/sessions")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }
    assert not RadicalSession.objects.filter(user=user).exists()
    assert RadicalSessionRadical.objects.count() == 0


def test_radicals_sessions_lists_existing_sessions(client):
    user = UserFactory.create()
    client.force_login(user)
    other_user = UserFactory.create()

    first_radical = seed_radical(1)
    second_radical = seed_radical(2)

    older_session = RadicalSession.objects.create(
        user=user,
        num_of_radicals=1,
        highest_score=40,
    )
    RadicalSessionRadical.objects.create(
        session=older_session,
        radical=first_radical,
        position=1,
    )

    newer_session = RadicalSession.objects.create(
        user=user,
        num_of_radicals=1,
        highest_score=95,
    )
    RadicalSessionRadical.objects.create(
        session=newer_session,
        radical=second_radical,
        position=1,
    )

    other_session = RadicalSession.objects.create(
        user=other_user,
        num_of_radicals=1,
        highest_score=70,
    )
    RadicalSessionRadical.objects.create(
        session=other_session,
        radical=seed_radical(3),
        position=1,
    )

    response = client.get("/api/radicals/sessions")

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    expected_session_ids = [str(newer_session.id), str(older_session.id)]
    assert payload["count"] == len(expected_session_ids)
    assert payload["next"] is None
    assert payload["previous"] is None
    assert [item["id"] for item in payload["results"]] == expected_session_ids
    assert str(other_session.id) not in [item["id"] for item in payload["results"]]


def test_radical_session_detail_returns_full_session_payload(client):
    user = UserFactory.create()
    client.force_login(user)
    expected_num_of_radicals = 7
    expected_highest_score = 88

    session = RadicalSession.objects.create(
        user=user,
        num_of_radicals=expected_num_of_radicals,
        highest_score=expected_highest_score,
    )

    response = client.get(f"/api/radicals/sessions/{session.id}")

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["id"] == str(session.id)
    assert "createdAt" in payload
    assert payload["numOfRadicals"] == expected_num_of_radicals
    assert payload["highestScore"] == expected_highest_score
    assert "created_at" not in payload
    assert "num_of_radicals" not in payload
    assert "highest_score" not in payload
