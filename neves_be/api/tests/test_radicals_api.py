from __future__ import annotations

from http import HTTPStatus

import pytest
from django.test import Client

from neves_be.radicals.models import Radical
from neves_be.radicals.models import RadicalSession
from neves_be.radicals.models import RadicalSessionRadical
from neves_be.radicals.models import RadicalSessionTest
from neves_be.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


RADICAL_IDS = ["人", "口", "土", "木", "火", "水", "金", "山"]
TEST_RADICAL_COUNT = 6
ANSWER_OPTION_COUNT = 5
MISSING_QUESTION_NUMBER = 999


def seed_radicals(count: int = TEST_RADICAL_COUNT) -> list[Radical]:
    radicals: list[Radical] = []
    for idx in range(count):
        radical = Radical.objects.create(
            id=RADICAL_IDS[idx],
            pinyin=f"ren{idx + 1}",
            meaning=f"meaning-{idx + 1}",
            main_representation=ord(RADICAL_IDS[idx]),
            other_vars=[],
            pronounce=f"/audio-cmn/18k-abr/syllabs/ren{idx + 1}.mp3",
        )
        radicals.append(radical)
    return radicals


def seed_session(user, radicals: list[Radical]) -> RadicalSession:
    session = RadicalSession.objects.create(user=user, num_of_radicals=len(radicals))
    RadicalSessionRadical.objects.bulk_create(
        [
            RadicalSessionRadical(session=session, radical=radical, position=position)
            for position, radical in enumerate(radicals, start=1)
        ],
    )
    return session


def test_radicals_sessions_requires_authentication(client: Client):
    response = client.get("/api/radicals/sessions")
    assert response.status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}


def test_create_test_and_question_contract(client: Client):
    user = UserFactory.create()
    client.force_login(user)

    radicals = seed_radicals(TEST_RADICAL_COUNT)
    session = seed_session(user, radicals)

    create_response = client.post(f"/api/radicals/sessions/{session.id}/tests")
    assert create_response.status_code == HTTPStatus.CREATED

    test_id = create_response.json()["id"]

    question_response = client.get(f"/api/radicals/test/{test_id}/question/1")
    assert question_response.status_code == HTTPStatus.OK

    payload = question_response.json()
    assert payload["count"] == TEST_RADICAL_COUNT
    assert payload["previous"] is None
    assert payload["next"] is not None
    assert payload["id"] == test_id
    assert payload["payload"]["type"] in {
        "AUDIO-TO-LOGOGRAM",
        "LOGOGRAM-TO-AUDIO",
        "LOGOGRAM-TO-MEANING",
        "LOGOGRAM-TO-PINYIN",
        "MEANING-TO-LOGOGRAM",
        "PINYIN-TO-LOGOGRAM",
    }
    assert len(payload["payload"]["alternatives"]) == ANSWER_OPTION_COUNT


def test_answer_validation_and_question_missed_payload(client: Client):
    user = UserFactory.create()
    client.force_login(user)

    radicals = seed_radicals(TEST_RADICAL_COUNT)
    session = seed_session(user, radicals)
    test_id = client.post(f"/api/radicals/sessions/{session.id}/tests").json()["id"]

    invalid_answer_response = client.post(
        f"/api/radicals/test/{test_id}/answer",
        data={"questionNum": 1, "answer": "z"},
        content_type="application/json",
    )
    assert invalid_answer_response.status_code == HTTPStatus.BAD_REQUEST
    assert invalid_answer_response.json()["code"] == "INVALID_ANSWER"

    missed_response = client.post(
        f"/api/radicals/test/{test_id}/answer",
        data={"questionNum": MISSING_QUESTION_NUMBER, "answer": "a"},
        content_type="application/json",
    )
    assert missed_response.status_code == HTTPStatus.CONFLICT
    assert missed_response.json()["code"] == "QUESTION_MISSED"
    assert (
        missed_response.json()["payload"]["questionMissed"] == MISSING_QUESTION_NUMBER
    )


def test_finish_requires_all_answers(client: Client):
    user = UserFactory.create()
    client.force_login(user)

    session = seed_session(user, seed_radicals(TEST_RADICAL_COUNT))
    test_id = client.post(f"/api/radicals/sessions/{session.id}/tests").json()["id"]

    response = client.post(f"/api/radicals/test/{test_id}/finish")
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "QUESTION_MISSED"
    assert response.json()["payload"]["questionMissed"] == 1


def test_finish_computes_score_and_result_contract(client: Client):
    user = UserFactory.create()
    client.force_login(user)

    session = seed_session(user, seed_radicals(TEST_RADICAL_COUNT))
    create_payload = client.post(f"/api/radicals/sessions/{session.id}/tests").json()
    test_id = create_payload["id"]

    first_question = client.get(f"/api/radicals/test/{test_id}/question/1").json()
    count = first_question["count"]

    for number in range(1, count + 1):
        answer_response = client.post(
            f"/api/radicals/test/{test_id}/answer",
            data={"questionNum": number, "answer": "a"},
            content_type="application/json",
        )
        assert answer_response.status_code == HTTPStatus.OK

    finish_response = client.post(f"/api/radicals/test/{test_id}/finish")
    assert finish_response.status_code == HTTPStatus.OK

    test = RadicalSessionTest.objects.get(id=test_id)
    assert test.finished_at is not None

    expected_correct = test.questions.filter(
        curr_answer="a",
        expected_answer="a",
    ).count()
    expected_score = round((expected_correct / count) * 100)
    assert test.score == expected_score

    result_response = client.get(f"/api/radicals/sessions/tests/{test_id}/result")
    assert result_response.status_code == HTTPStatus.OK
    result_payload = result_response.json()
    assert result_payload["id"] == test_id
    assert result_payload["score"] == expected_score
    assert len(result_payload["questions"]) == count
    assert "currAnswer" in result_payload["questions"][0]
    assert "expectedAnswer" in result_payload["questions"][0]


def test_user_cannot_access_other_users_test(client: Client):
    owner = UserFactory.create()
    other_user = UserFactory.create()

    owner_client = Client()
    owner_client.force_login(owner)
    session = seed_session(owner, seed_radicals(TEST_RADICAL_COUNT))
    test_id = owner_client.post(f"/api/radicals/sessions/{session.id}/tests").json()[
        "id"
    ]

    client.force_login(other_user)
    response = client.get(f"/api/radicals/test/{test_id}/question/1")
    assert response.status_code == HTTPStatus.NOT_FOUND
