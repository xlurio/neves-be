from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import assert_never
from typing import cast

from django.db import transaction

from neves_be.language_model.models import Radical
from neves_be.practice_assessments.constants import ANSWER_CHOICES
from neves_be.practice_assessments.constants import ASSESSMENT_QUESTION_COUNT
from neves_be.practice_assessments.constants import MINIMUM_ASSESSMENT_POOL_SIZE
from neves_be.practice_assessments.exceptions import CreateRadicalSessionAssessmentError
from neves_be.practice_assessments.models import PracticeSessionAssessmentQuestionAlt
from neves_be.practice_assessments.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_assessments.models import RadicalSessionAssessmentQuestion
from neves_be.practice_assessments.services.assessments import BaseAssessmentAccessor
from neves_be.practice_assessments.services.assessments import BaseAssessmentFactory
from neves_be.practice_assessments.services.assessments import safe_pronounce_url
from neves_be.radical_sessions.models import RadicalSessionRadical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_assessments.types import RadicalAssessmentQuestionType
    from neves_be.practice_sessions.types import ConcretePracticeSession
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


class RadicalAssessmentAccessor(BaseAssessmentAccessor):
    NOT_FOUND_ERROR_MSG = "Radical test not found."
    ASSESSMENT_TYPE = RadicalSessionAssessment


class RadicalAssessmentFactory(BaseAssessmentFactory):
    def __init__(self, request: Request) -> None:
        self.__request = request

    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _session = cast("RadicalSession", session)
        session_radicals = self.__get_session_radicals(_session)
        pool = list(Radical.objects.order_by("id"))
        if len(pool) < MINIMUM_ASSESSMENT_POOL_SIZE or not session_radicals:
            raise CreateRadicalSessionAssessmentError(
                code="NOT_ENOUGH_RADICALS",
                title="Assessment locked",
                details="At least five radicals are required to generate a test.",
            )

        with transaction.atomic():
            assessment = RadicalSessionAssessment.objects.create(session=_session)
            rng = random.Random(assessment.id.int)
            assessment_radicals = self.__select_assessment_radicals(
                session_radicals,
                rng,
            )
            questions = []
            alternatives_to_create: list[PracticeSessionAssessmentQuestionAlt] = []
            for number, radical in enumerate(assessment_radicals, start=1):
                question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
                options = self.__pick_option_radicals(radical, pool, rng)
                alternatives = self.__build_alternatives(
                    self.__request,
                    question_type,
                    options,
                )
                question = (
                    RadicalSessionAssessmentQuestion.objects.create(  # type: ignore[misc]
                        assessment=assessment,
                        number=number,
                        type=question_type,
                        question=self.__question_text(radical, question_type),
                        audio=radical.pronounce
                        if question_type
                        == RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM
                        else "",
                        expected_answer=ANSWER_CHOICES[options.index(radical)],
                    ),
                )
                questions.append(question)

                for alt in alternatives:
                    alt.question = question
                    alternatives_to_create.append(alt)

            PracticeSessionAssessmentQuestionAlt.objects.bulk_create(
                alternatives_to_create,
            )

        return assessment

    def __get_session_radicals(self, session: RadicalSession) -> list[Radical]:
        return [
            session_radical.radical
            for session_radical in RadicalSessionRadical.objects.filter(
                session__user=session.user,
            )
            .select_related(
                "radical",
            )
            .order_by("position")
        ]

    def __select_assessment_radicals(
        self,
        session_radicals: list[Radical],
        rng: random.Random,
    ) -> list[Radical]:
        if len(session_radicals) >= ASSESSMENT_QUESTION_COUNT:
            return rng.sample(session_radicals, k=ASSESSMENT_QUESTION_COUNT)
        return [rng.choice(session_radicals) for _ in range(ASSESSMENT_QUESTION_COUNT)]

    def __pick_option_radicals(
        self,
        correct: Radical,
        pool: list[Radical],
        rng: random.Random,
    ) -> list[Radical]:
        distractors = [radical for radical in pool if radical.id != correct.id]
        selected = rng.sample(distractors, k=4)
        options = [*selected, correct]
        rng.shuffle(options)
        return options

    def __question_text(
        self,
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

    def __build_alternatives(
        self,
        request: Request,
        question_type: RadicalAssessmentQuestionType,
        options: list[Radical],
    ) -> list[PracticeSessionAssessmentQuestionAlt]:
        alt_letters = set(PracticeSessionAssessmentQuestionAnswer)
        alternatives: set[PracticeSessionAssessmentQuestionAlt] = {}

        for ltt_idx, option in enumerate(options):
            if question_type == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO:
                alternatives.add(
                    PracticeSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="AUDIO",
                        payload=safe_pronounce_url(request, option.pronounce),
                    ),
                )
            elif (
                question_type
                == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING
            ):
                alternatives.add(
                    PracticeSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.meaning,
                    ),
                )
            elif (
                question_type
                == RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN
            ):
                alternatives.add(
                    PracticeSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.pinyin,
                    ),
                )
            elif question_type in {
                RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM,
                RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM,
                RadicalSessionAssessmentQuestion.Type.PINYIN_TO_LOGOGRAM,
            }:
                alternatives.add(
                    PracticeSessionAssessmentQuestionAlt(
                        letter=alt_letters[ltt_idx],
                        type="TEXT",
                        payload=option.id,
                    ),
                )
            else:
                assert_never(question_type)
