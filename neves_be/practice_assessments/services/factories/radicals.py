from __future__ import annotations

import random
from typing import TYPE_CHECKING
from typing import cast

from django.db import transaction

from neves_be.language_model.models import Radical
from neves_be.practice_assessments.constants import ASSESSMENT_QUESTION_COUNT
from neves_be.practice_assessments.constants import MINIMUM_ASSESSMENT_POOL_SIZE
from neves_be.practice_assessments.exceptions import CreateRadicalSessionAssessmentError
from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_assessments.services.factories.base import BaseAssessmentFactory
from neves_be.practice_assessments.services.radical_questions import (
    RadicalQuestionFactory,
)
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestionAlt
from neves_be.radical_sessions.models import RadicalSessionRadical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.radical_sessions.models import RadicalSession


class RadicalAssessmentFactory(BaseAssessmentFactory):
    def __init__(self, request: Request) -> None:
        self.__request = request

    @transaction.atomic()
    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _session = cast("RadicalSession", session)
        session_radicals = self.__get_session_radicals(_session)
        radical_pool = list(Radical.objects.order_by("id"))
        if len(radical_pool) < MINIMUM_ASSESSMENT_POOL_SIZE or not session_radicals:
            raise CreateRadicalSessionAssessmentError(
                code="NOT_ENOUGH_RADICALS",
                title="Assessment locked",
                details="At least five radicals are required to generate a test.",
            )

        assessment = RadicalSessionAssessment.objects.create(session=_session)
        rng = random.Random(assessment.id.int)
        assessment_radicals = self.__select_assessment_radicals(
            session_radicals,
            rng,
        )

        alternatives_to_create: list[RadicalSessionAssessmentQuestionAlt] = []
        for number, radical in enumerate(assessment_radicals, start=1):
            question_rst = RadicalQuestionFactory(
                request=self.__request,
                radical=radical,
                radical_pool=radical_pool,
                rng=rng,
            ).make_question(assessment, number)

            alternatives_to_create.extend(question_rst["alternatives"])

        RadicalSessionAssessmentQuestionAlt.objects.bulk_create(
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
