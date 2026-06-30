from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import cast

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.practice_assessments.exceptions import (
    CreateSentenceSessionAssessmentError,
)
from neves_be.practice_assessments.models import SentenceSessionAssessment
from neves_be.practice_assessments.services.chr2rdc_questions import (
    Char2RadicalQuestionFactory,
)
from neves_be.practice_assessments.services.factories.base import BaseAssessmentFactory
from neves_be.practice_assessments.services.snt2wrd_questions import (
    Sentence2WordQuestionFactory,
)
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestion
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestionAlt
from neves_be.practice_questions.models import SentenceSessionQuestionType
from neves_be.sentence_sessions.models import SentenceSession

if TYPE_CHECKING:
    from collections.abc import Sequence

    from django.db import models

    from neves_be.language_model.types import SentenceId
    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.users.models import User


class SentenceAssessmentFactory(BaseAssessmentFactory):
    NUM_OF_QUESTIONS = 10
    MINIMUM_WORDS_LEARNED_RATE = 0.8
    MAXIMUM_ITERATIONS = 1e3

    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment:
        _session = cast("SentenceSession", session)
        assessment_sentences = self.__get_valid_sentences(_session)

        assessment = SentenceSessionAssessment.objects.create(
            session=_session,
        )
        self.__make_questions(assessment, assessment_sentences)

        return assessment

    def __get_valid_sentences(self, session: SentenceSession) -> Sequence[Sentence]:
        words_learned = set(
            Word.objects.filter(
                word_sentences__sentence__sentence_sessions__session__isnull=False,
            ),
        )

        _user = session.user

        assert _user

        snt_word_mapping = self.__make_snt_wrd_mapping_from_snt_cluster(
            _user,
        )
        snts_lrn_by_user = list(self.__get_learned_sentences_qs(_user))
        assessment_sentences: set[Sentence] = set()
        curr_iters = 0

        while len(assessment_sentences) < self.NUM_OF_QUESTIONS:
            curr_iters += 1

            curr_sentence = random.choice(snts_lrn_by_user)
            words_in_sentence = len(snt_word_mapping[curr_sentence.id])
            words_learning_in_sentence = len(
                words_learned.intersection(snt_word_mapping[curr_sentence.id]),
            )

            if (
                words_learning_in_sentence
                >= words_in_sentence * self.MINIMUM_WORDS_LEARNED_RATE
            ):
                assessment_sentences.add(curr_sentence)
            else:
                snts_lrn_by_user.remove(curr_sentence)

            if curr_iters >= self.MAXIMUM_ITERATIONS:
                raise CreateSentenceSessionAssessmentError(
                    code="NOT_ENOUGH_SENTENCES",
                    title="Assessment locked",
                    details="Learn more sentences to unlock this assessment",
                )

        return cast("Sequence[Sentence]", assessment_sentences)

    def __make_snt_wrd_mapping_from_snt_cluster(
        self,
        user: User,
    ) -> dict[SentenceId, list[Word]]:
        snt_wrd_pairs = set(
            WordSentenceMap.objects.filter(
                sentence_id=self.__get_learned_sentences_qs(user).values_list(
                    "pk",
                    flat=True,
                ),
            ),
        )
        result: dict[SentenceId, list[Word]] = defaultdict(list)

        for snt_wrd_pair in snt_wrd_pairs:
            result[cast("SentenceId", snt_wrd_pair.sentence_id)].append(
                snt_wrd_pair.word,
            )

        return result

    def __get_learned_sentences_qs(self, user: User) -> models.QuerySet[Sentence]:
        user_sessions = SentenceSession.objects.filter(user=user)
        return Sentence.objects.filter(
            sentence_sessions__session_id__in=user_sessions.values_list(
                "pk",
                flat=True,
            ),
        )

    def __make_questions(
        self,
        assessment: SentenceSessionAssessment,
        sentences: Sequence[Sentence],
    ) -> Sequence[SentenceSessionAssessmentQuestion]:
        questions = set()
        alternatives_to_create = []
        number = 1
        question_type = random.choice(SentenceSessionQuestionType)

        for sentence in sentences:
            if question_type == SentenceSessionQuestionType.LOGOGRAM_TO_RADICALS:
                rst = Char2RadicalQuestionFactory(sentence).make_question(
                    assessment,
                    number,
                )

            else:
                rst = Sentence2WordQuestionFactory(
                    sentence,
                    question_type,
                ).make_question(
                    assessment,
                    number,
                )

            questions.add(rst["question"])
            alternatives_to_create.extend(rst["alternatives"])

            number += 1

        SentenceSessionAssessmentQuestionAlt.objects.bulk_create(alternatives_to_create)

        return cast("Sequence[SentenceSessionAssessmentQuestion]", questions)
