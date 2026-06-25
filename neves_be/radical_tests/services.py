from __future__ import annotations

import random
from typing import TYPE_CHECKING

from django.db import transaction
from django.shortcuts import get_object_or_404

from neves_be.radical_sessions.services import get_session_radicals
from neves_be.radical_tests.models import RadicalSessionTest
from neves_be.radical_tests.models import RadicalSessionTestQuestion
from neves_be.radicals.models import Radical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.radical_sessions.models import RadicalSession

ANSWER_CHOICES = ["a", "b", "c", "d", "e"]
MINIMUM_TEST_POOL_SIZE = len(ANSWER_CHOICES)
QUESTION_TYPES = [
    RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN,
    RadicalSessionTestQuestion.Type.MEANING_TO_LOGOGRAM,
    RadicalSessionTestQuestion.Type.PINYIN_TO_LOGOGRAM,
]


def safe_pronounce_url(request: Request, pronounce: str) -> str:
    if not pronounce:
        return ""
    if pronounce.startswith(("http://", "https://")):
        return pronounce
    if pronounce.startswith("/"):
        return request.build_absolute_uri(pronounce)
    return pronounce


def pick_option_radicals(
    correct: Radical,
    pool: list[Radical],
    rng: random.Random,
) -> list[Radical]:
    distractors = [radical for radical in pool if radical.id != correct.id]
    selected = rng.sample(distractors, k=4)
    options = [*selected, correct]
    rng.shuffle(options)
    return options


def question_text(radical: Radical, question_type: str) -> str:
    if question_type == RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM:
        return "What logogram corresponds to the following audio?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO:
        return f"What pronounce corresponds the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING:
        return f"What meaning corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN:
        return f"What pinyin corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.MEANING_TO_LOGOGRAM:
        return f'What logogram corresponds to the meaning "{radical.meaning}"?'
    return f'What logogram corresponds to the pinyin "{radical.pinyin}"?'


def build_alternatives(
    request: Request,
    question_type: str,
    options: list[Radical],
) -> list[dict[str, str]]:
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO:
        return [
            {"type": "AUDIO", "payload": safe_pronounce_url(request, option.pronounce)}
            for option in options
        ]
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING:
        return [{"type": "TEXT", "payload": option.meaning} for option in options]
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN:
        return [{"type": "TEXT", "payload": option.pinyin} for option in options]
    return [{"type": "TEXT", "payload": option.id} for option in options]


def serialize_question_payload(
    question: RadicalSessionTestQuestion,
    request: Request,
) -> dict:
    payload: dict[str, object] = {
        "type": question.type,
        "question": question.question,
        "alternatives": question.alternatives,
        "currAnswer": question.curr_answer,
    }
    if question.audio:
        payload["audio"] = safe_pronounce_url(request, question.audio)
    return payload


def owned_test_or_404(request: Request, test_id) -> RadicalSessionTest:
    return get_object_or_404(
        RadicalSessionTest.objects.select_related("session"),
        id=test_id,
        session__user=request.user,
    )


def create_session_test(
    session: RadicalSession,
    request: Request,
) -> RadicalSessionTest:
    session_radicals = get_session_radicals(session)
    pool = list(Radical.objects.order_by("id"))
    if len(pool) < MINIMUM_TEST_POOL_SIZE or not session_radicals:
        msg = "At least five radicals are required to generate a test."
        raise ValueError(msg)

    with transaction.atomic():
        test = RadicalSessionTest.objects.create(session=session)
        rng = random.Random(test.id.int)
        questions = []
        for number, radical in enumerate(session_radicals, start=1):
            question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
            options = pick_option_radicals(radical, pool, rng)
            questions.append(
                RadicalSessionTestQuestion(
                    test=test,
                    number=number,
                    type=question_type,
                    question=question_text(radical, question_type),
                    alternatives=build_alternatives(request, question_type, options),
                    audio=radical.pronounce
                    if question_type
                    == RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM
                    else "",
                    expected_answer=ANSWER_CHOICES[options.index(radical)],
                ),
            )
        RadicalSessionTestQuestion.objects.bulk_create(questions)
    return test


def serialize_result_questions(
    test: RadicalSessionTest,
    request: Request,
) -> list[dict[str, object]]:
    questions = []
    for question in test.questions.order_by("number"):
        payload: dict[str, object] = {
            "type": question.type,
            "question": question.question,
            "alternatives": question.alternatives,
            "currAnswer": question.curr_answer or "a",
            "expectedAnswer": question.expected_answer,
        }
        if question.audio:
            payload["audio"] = safe_pronounce_url(request, question.audio)
        questions.append(payload)
    return questions
