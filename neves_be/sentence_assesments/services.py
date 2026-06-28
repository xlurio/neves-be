from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import cast

from django.db import transaction
from django.http import Http404

from neves_be.language_model.models import Sentence
from neves_be.radical_assesments.services import ANSWER_CHOICES
from neves_be.radical_assesments.services import ASSESSMENT_QUESTION_COUNT
from neves_be.radical_assesments.services import MINIMUM_ASSESSMENT_POOL_SIZE
from neves_be.sentence_assesments.models import SentenceSessionAssessment
from neves_be.sentence_assesments.models import SentenceSessionAssessmentQuestion
from neves_be.sentence_sessions.services import get_session_sentences

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assesments.types import AlternativePayload
    from neves_be.practice_assesments.types import AnswerChoice
    from neves_be.practice_assesments.types import CurrentAnswer
    from neves_be.sentence_assesments.types import SentenceAssessmentQuestionType
    from neves_be.sentence_assesments.types import (
        SentenceResultAssessmentQuestionPayload,
    )
    from neves_be.sentence_assesments.types import SentenceSessionAssessmentId
    from neves_be.sentence_sessions.models import SentenceSession

QUESTION_TYPES: tuple[SentenceAssessmentQuestionType, ...] = (
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_AUDIO,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_AUDIO,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_TEXT,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_TEXT,
    ),
    cast(
        "SentenceAssessmentQuestionType",
        SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_RADICALS,
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


def pick_option_sentences(
    correct: Sentence,
    pool: list[Sentence],
    rng: random.Random,
) -> list[Sentence]:
    distractors = [sentence for sentence in pool if sentence.id != correct.id]
    selected = rng.sample(distractors, k=4)
    options = [*selected, correct]
    rng.shuffle(options)
    return options


def question_text(
    sentence: Sentence,
    question_type: SentenceAssessmentQuestionType,
) -> str:
    if question_type == SentenceSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM:
        return "What logogram corresponds to the following audio?"
    if question_type == SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
        return f"What pronounce corresponds the logogram {sentence.id}?"
    if question_type == SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING:
        return f"What meaning corresponds to the logogram {sentence.id}?"
    if question_type == SentenceSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN:
        return f"What pinyin corresponds to the logogram {sentence.id}?"
    if question_type == SentenceSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM:
        return f'What logogram corresponds to the meaning "{sentence.meaning}"?'
    return f'What logogram corresponds to the pinyin "{sentence.pinyin}"?'


def build_alternatives(
    request: Request,
    question_type: SentenceAssessmentQuestionType,
    options: list[Sentence],
) -> list[AlternativePayload]:
    if question_type in {
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_AUDIO,
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_AUDIO,
    }:
        return [
            {"type": "AUDIO", "payload": safe_pronounce_url(request, option.pronounce)}
            for option in options
        ]
    if question_type in {
        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_TEXT,
        SentenceSessionAssessmentQuestion.Type.SENTENCE_TEXT_TO_WORD_TEXT,
    }:
        return [{"type": "TEXT", "payload": option.value} for option in options]

    return [{"type": "TEXT", "payload": option.id} for option in options]


def serialize_question_payload(
    question: SentenceSessionAssessmentQuestion,
    request: Request,
) -> SentenceAssessmentQuestionType:
    payload: SentenceAssessmentQuestionType = {
        "type": cast("SentenceAssessmentQuestionType", question.type),
        "question": question.question,
        "alternatives": cast("list[AlternativePayload]", question.alternatives),
        "currAnswer": _current_answer(question.curr_answer),
    }
    if question.audio:
        payload["audio"] = safe_pronounce_url(request, question.audio)
    return payload


def owned_assessment_or_404(
    request: Request,
    assessment_id: SentenceSessionAssessmentId,
) -> SentenceSessionAssessment:
    test = (
        SentenceSessionAssessment.objects.select_related("session")
        .filter(
            id=assessment_id,
            session__user=request.user,
        )
        .first()
    )
    if test is None:
        msg = "Sentence test not found."
        raise Http404(msg)
    return test


def select_assessment_sentences(
    session_sentences: list[Sentence],
    rng: random.Random,
) -> list[Sentence]:
    if len(session_sentences) >= ASSESSMENT_QUESTION_COUNT:
        return rng.sample(session_sentences, k=ASSESSMENT_QUESTION_COUNT)
    return [rng.choice(session_sentences) for _ in range(ASSESSMENT_QUESTION_COUNT)]


def create_session_assessment(
    session: SentenceSession,
    request: Request,
) -> SentenceSessionAssessment:
    session_sentences = get_session_sentences(session)
    pool = list(Sentence.objects.order_by("id"))
    if len(pool) < MINIMUM_ASSESSMENT_POOL_SIZE or not session_sentences:
        msg = "At least five sentences are required to generate a test."
        raise ValueError(msg)

    with transaction.atomic():
        test = SentenceSessionAssessment.objects.create(session=session)
        rng = random.Random(test.id.int)
        assessment_sentences = select_assessment_sentences(session_sentences, rng)
        questions = []
        for number, sentence in enumerate(assessment_sentences, start=1):
            question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
            options = pick_option_sentences(sentence, pool, rng)
            questions.append(
                SentenceSessionAssessmentQuestion(
                    test=test,
                    number=number,
                    type=question_type,
                    question=question_text(sentence, question_type),
                    alternatives=build_alternatives(request, question_type, options),
                    audio=sentence.pronounce
                    if question_type
                    in {
                        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_AUDIO,
                        SentenceSessionAssessmentQuestion.Type.SENTENCE_AUDIO_TO_WORD_TEXT,
                    }
                    else "",
                    expected_answer=ANSWER_CHOICES[options.index(sentence)],
                ),
            )
        SentenceSessionAssessmentQuestion.objects.bulk_create(questions)
    return test


def serialize_result_questions(
    test: SentenceSessionAssessment,
    request: Request,
) -> list[SentenceResultAssessmentQuestionPayload]:
    questions = []
    for question in test.questions.order_by("number"):
        payload: SentenceResultAssessmentQuestionPayload = {
            "type": cast("SentenceAssessmentQuestionType", question.type),
            "question": question.question,
            "alternatives": cast("list[AlternativePayload]", question.alternatives),
            "currAnswer": cast("AnswerChoice", question.curr_answer or "a"),
            "expectedAnswer": cast("AnswerChoice", question.expected_answer),
        }
        if question.audio:
            payload["audio"] = safe_pronounce_url(request, question.audio)
        questions.append(payload)
    return questions
