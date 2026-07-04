from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING
from typing import cast

from django.db import models
from django.db import transaction

from neves_be.practice_assessments.models import NgramSessionAssessment
from neves_be.practice_assessments.services.chr2rdc_questions import (
    Char2RadicalQuestionFactory,
)
from neves_be.practice_assessments.services.factories.base import BaseAssessmentFactory
from neves_be.practice_assessments.services.snt2wrd_questions import (
    Ngram2WordQuestionFactory,
)
from neves_be.practice_questions.models import NgramSessionAssessmentQuestion
from neves_be.practice_questions.models import NgramSessionAssessmentQuestionAlt
from neves_be.practice_questions.models import NgramSessionQuestionType
from neves_be.word_lm.models import Ngram

if TYPE_CHECKING:
    from collections.abc import Sequence

    from neves_be.ngram_sessions.models import NgramSession
    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_sessions.types import ConcretePracticeSession


class NgramAssessmentFactory(BaseAssessmentFactory):
    NUM_OF_QUESTIONS = 10
    MAXIMUM_ITERATIONS = 1e3

    @transaction.atomic()
    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _logger = logging.getLogger(self.make_assessment.__name__)
        _logger.info("Creating n-gram assessment")

        _session = cast("NgramSession", session)
        assessment_ngrams = self.__get_valid_ngrams(_session)

        assessment = NgramSessionAssessment.objects.create(
            session=_session,
        )
        self.__make_questions(assessment, assessment_ngrams)

        return assessment

    def __get_valid_ngrams(self, session: NgramSession) -> Sequence[Ngram]:
        _user = session.user
        assert _user

        return random.sample(
            list(
                Ngram.objects.filter(
                    models.Q(ngram_sessions__session=session)
                    | models.Q(
                        ngram_sessions__session__user=_user,
                        ngram_sessions__session__highest_score__gte=70,
                    ),
                ).distinct(),
            ),
            k=10,
        )

    def __make_questions(
        self,
        assessment: NgramSessionAssessment,
        ngrams: Sequence[Ngram],
    ) -> Sequence[NgramSessionAssessmentQuestion]:
        _logger = logging.getLogger(self.make_assessment.__name__)
        _logger.info("Creating n-gram assessment questions")

        questions = set()
        alternatives_to_create: list[NgramSessionAssessmentQuestionAlt] = []
        question_type = random.choice(list(NgramSessionQuestionType))

        for question_idx, ngram in enumerate(ngrams):
            _logger.info("Creating n-gram assessment question %d", question_idx)

            if question_type == NgramSessionQuestionType.LOGOGRAM_TO_RADICALS:
                rst = Char2RadicalQuestionFactory().make_question(
                    assessment,
                    question_idx + 1,
                )

            else:
                rst = Ngram2WordQuestionFactory(
                    ngram,
                    question_type,
                ).make_question(
                    assessment,
                    question_idx + 1,
                )

            questions.add(rst["question"])
            alternatives_to_create.extend(
                cast(
                    "Sequence[NgramSessionAssessmentQuestionAlt]",
                    rst["alternatives"],
                ),
            )

        NgramSessionAssessmentQuestionAlt.objects.bulk_create(alternatives_to_create)

        return cast("Sequence[NgramSessionAssessmentQuestion]", questions)
