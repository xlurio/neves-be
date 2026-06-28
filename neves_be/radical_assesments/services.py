from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import cast

from django.db import transaction
from django.http import Http404

from neves_be.language_model.models import Radical
from neves_be.practice_assesments.constants import ANSWER_CHOICES
from neves_be.practice_assesments.constants import ASSESSMENT_QUESTION_COUNT
from neves_be.practice_assesments.constants import MINIMUM_ASSESSMENT_POOL_SIZE
from neves_be.radical_assesments.models import RadicalSessionAssessment
from neves_be.radical_assesments.models import RadicalSessionAssessmentQuestion
from neves_be.radical_sessions.services import get_session_radicals

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assesments.types import AlternativePayload
    from neves_be.practice_assesments.types import AnswerChoice
    from neves_be.practice_assesments.types import AssessmentId
    from neves_be.practice_assesments.types import CurrentAnswer
    from neves_be.radical_assesments.types import RadicalAssessmentQuestionPayload
    from neves_be.radical_assesments.types import RadicalAssessmentQuestionType
    from neves_be.radical_sessions.models import RadicalSession

QUESTION_TYPES: tuple[RadicalAssessmentQuestionType, ...] = (
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.PINYIN_TO_LOGOGRAM,
    ),
)


def _current_answer(value: str) -> CurrentAnswer:
    if value in ANSWER_CHOICES:
        return value
    return ""


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


def question_text(
    radical: Radical,
    question_type: RadicalAssessmentQuestionType,
) -> str:
    if question_type == RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM:
        return "What logogram corresponds to the following audio?"
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
        return f"What pronounce corresponds the logogram {radical.id}?"
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING:
        return f"What meaning corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN:
        return f"What pinyin corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM:
        return f'What logogram corresponds to the meaning "{radical.meaning}"?'
    return f'What logogram corresponds to the pinyin "{radical.pinyin}"?'


def build_alternatives(
    request: Request,
    question_type: RadicalAssessmentQuestionType,
    options: list[Radical],
) -> list[AlternativePayload]:
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
        return [
            {"type": "AUDIO", "payload": safe_pronounce_url(request, option.pronounce)}
            for option in options
        ]
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING:
        return [{"type": "TEXT", "payload": option.meaning} for option in options]
    if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN:
        return [{"type": "TEXT", "payload": option.pinyin} for option in options]
    return [{"type": "TEXT", "payload": option.id} for option in options]


def serialize_question_payload(
    question: RadicalSessionAssessmentQuestion,
    request: Request,
) -> RadicalAssessmentQuestionPayload:
    payload: RadicalAssessmentQuestionPayload = {
        "type": cast("RadicalAssessmentQuestionType", question.type),
        "question": question.question,
        "alternatives": cast("list[AlternativePayload]", question.alternatives),
        "currAnswer": _current_answer(question.curr_answer),
    }
    if question.audio:
        payload["audio"] = safe_pronounce_url(request, question.audio)
    return payload


def owned_assessment_or_404(
    request: Request,
    assessment_id: AssessmentId,
) -> RadicalSessionAssessment:
    test = (
        RadicalSessionAssessment.objects.select_related("session")
        .filter(
            id=assessment_id,
            session__user=request.user,
        )
        .first()
    )
    if test is None:
        msg = "Radical test not found."
        raise Http404(msg)
    return test


def select_assessment_radicals(
    session_radicals: list[Radical],
    rng: random.Random,
) -> list[Radical]:
    if len(session_radicals) >= ASSESSMENT_QUESTION_COUNT:
        return rng.sample(session_radicals, k=ASSESSMENT_QUESTION_COUNT)
    return [rng.choice(session_radicals) for _ in range(ASSESSMENT_QUESTION_COUNT)]


def create_session_assessment(
    session: RadicalSession,
    request: Request,
) -> RadicalSessionAssessment:
    session_radicals = get_session_radicals(session)
    pool = list(Radical.objects.order_by("id"))
    if len(pool) < MINIMUM_ASSESSMENT_POOL_SIZE or not session_radicals:
        msg = "At least five radicals are required to generate a test."
        raise ValueError(msg)

    with transaction.atomic():
        test = RadicalSessionAssessment.objects.create(session=session)
        rng = random.Random(test.id.int)
        assessment_radicals = select_assessment_radicals(session_radicals, rng)
        questions = []
        for number, radical in enumerate(assessment_radicals, start=1):
            question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
            options = pick_option_radicals(radical, pool, rng)
            questions.append(
                RadicalSessionAssessmentQuestion(
                    test=test,
                    number=number,
                    type=question_type,
                    question=question_text(radical, question_type),
                    alternatives=build_alternatives(request, question_type, options),
                    audio=radical.pronounce
                    if question_type
                    == RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM
                    else "",
                    expected_answer=ANSWER_CHOICES[options.index(radical)],
                ),
            )
        RadicalSessionAssessmentQuestion.objects.bulk_create(questions)
    return test


def serialize_result_questions(
    test: RadicalSessionAssessment,
    request: Request,
) -> list[RadicalAssessmentQuestionPayload]:
    questions = []
    for question in test.questions.order_by("number"):
        payload: RadicalAssessmentQuestionPayload = {
            "type": cast("RadicalAssessmentQuestionType", question.type),
            "question": question.question,
            "alternatives": cast("list[AlternativePayload]", question.alternatives),
            "currAnswer": cast("AnswerChoice", question.curr_answer or "a"),
            "expectedAnswer": cast("AnswerChoice", question.expected_answer),
        }
        if question.audio:
            payload["audio"] = safe_pronounce_url(request, question.audio)
        questions.append(payload)
    return questions
