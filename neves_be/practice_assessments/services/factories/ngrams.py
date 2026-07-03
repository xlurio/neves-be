from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import cast

from django.db import transaction

from neves_be.ngram_sessions.models import NgramSession
from neves_be.practice_assessments.exceptions import CreateNgramSessionAssessmentError
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
from neves_be.word_lm.models import Word
from neves_be.word_lm.models import WordNgramMap

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db import models

    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.users.models import User
    from neves_be.word_lm.types import NgramId


class NgramAssessmentFactory(BaseAssessmentFactory):
    NUM_OF_QUESTIONS = 10
    MINIMUM_WORDS_LEARNED_RATE = 0.8
    MAXIMUM_ITERATIONS = 1e3

    @transaction.atomic()
    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _session = cast("NgramSession", session)
        assessment_ngrams = self.__get_valid_ngrams(_session)

        assessment = NgramSessionAssessment.objects.create(
            session=_session,
        )
        self.__make_questions(assessment, assessment_ngrams)

        return assessment

    def __get_valid_ngrams(self, session: NgramSession) -> Sequence[Ngram]:
        words_learned = set(
            Word.objects.filter(
                word_ngrams__ngram__ngram_sessions__session__isnull=False,
            ),
        )

        _user = session.user

        assert _user

        ngr_word_mapping = self.__make_ngr_wrd_mapping_from_ngr_cluster(
            _user,
        )
        ngrs_lrn_by_user = list(self.__get_learned_ngrams_qs(_user))
        assessment_ngrams: set[Ngram] = set()
        curr_iters = 0

        while len(assessment_ngrams) < self.NUM_OF_QUESTIONS:
            curr_iters += 1

            curr_ngram = random.choice(ngrs_lrn_by_user)
            words_in_ngram = len(ngr_word_mapping[curr_ngram.id])
            words_learning_in_ngram = len(
                words_learned.intersection(ngr_word_mapping[curr_ngram.id]),
            )

            if (
                words_learning_in_ngram
                >= words_in_ngram * self.MINIMUM_WORDS_LEARNED_RATE
            ):
                assessment_ngrams.add(curr_ngram)
            else:
                ngrs_lrn_by_user.remove(curr_ngram)

            if curr_iters >= self.MAXIMUM_ITERATIONS:
                raise CreateNgramSessionAssessmentError(
                    code="NOT_ENOUGH_NGRAMS",
                    title="Assessment locked",
                    details="Learn more ngrams to unlock this assessment",
                )

        return cast("Sequence[Ngram]", assessment_ngrams)

    def __make_ngr_wrd_mapping_from_ngr_cluster(
        self,
        user: User,
    ) -> dict[NgramId, list[Word]]:
        ngr_wrd_pairs = set(
            WordNgramMap.objects.filter(
                ngram_id=self.__get_learned_ngrams_qs(user).values_list(
                    "pk",
                    flat=True,
                ),
            ),
        )
        result: dict[NgramId, list[Word]] = defaultdict(list)

        for ngr_wrd_pair in ngr_wrd_pairs:
            result[ngr_wrd_pair.ngram_id].append(
                ngr_wrd_pair.word,
            )

        return result

    def __get_learned_ngrams_qs(self, user: User) -> models.QuerySet[Ngram]:
        user_sessions = NgramSession.objects.filter(user=user)

        lrnd_wrds = Word.objects.filter(
            word_ngrams__ngram__ngram_sessions__in=user_sessions,
        )

        return Ngram.objects.filter(ngram_words__word__in=lrnd_wrds)

    def __make_questions(
        self,
        assessment: NgramSessionAssessment,
        ngrams: Sequence[Ngram],
    ) -> Sequence[NgramSessionAssessmentQuestion]:
        questions = set()
        alternatives_to_create: list[NgramSessionAssessmentQuestionAlt] = []
        number = 1
        question_type = random.choice(list(NgramSessionQuestionType))

        for ngram in ngrams:
            if question_type == NgramSessionQuestionType.LOGOGRAM_TO_RADICALS:
                rst = Char2RadicalQuestionFactory().make_question(
                    assessment,
                    number,
                )

            else:
                rst = Ngram2WordQuestionFactory(
                    ngram,
                    question_type,
                ).make_question(
                    assessment,
                    number,
                )

            questions.add(rst["question"])
            alternatives_to_create.extend(
                cast(
                    "Sequence[NgramSessionAssessmentQuestionAlt]",
                    rst["alternatives"],
                ),
            )

            number += 1

        NgramSessionAssessmentQuestionAlt.objects.bulk_create(alternatives_to_create)

        return cast("Sequence[NgramSessionAssessmentQuestion]", questions)
