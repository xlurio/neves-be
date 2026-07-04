from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import cast

from neves_be.char_lm.models import Radical
from neves_be.char_lm.models import RadicalLogogramMap
from neves_be.practice_assessments.services.questions import AlternativesSetup
from neves_be.practice_assessments.services.questions import BasePracticeQuestionFactory
from neves_be.practice_assessments.services.questions import PracticeQuestionSetup
from neves_be.practice_questions.models import NgramSessionAssessmentQuestion
from neves_be.practice_questions.models import NgramSessionAssessmentQuestionAlt
from neves_be.practice_questions.models import PracticeAssessmentAlternativeTypeChoices
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.word_lm.models import Logogram

if TYPE_CHECKING:
    from collections.abc import Sequence

    from neves_be.char_lm.types import LogogramId
    from neves_be.ngram_sessions.models import NgramSession
    from neves_be.practice_assessments.models import NgramSessionAssessment
    from neves_be.practice_assessments.models import PracticeSessionAssessment


class Char2RadicalQuestionFactory(BasePracticeQuestionFactory):
    def _setup_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        _assessment = cast("NgramSessionAssessment", assessment)
        del assessment

        selected_logograms = self.__select_logograms(_assessment.session)
        question_logogram = selected_logograms[random.randint(0, 4)]
        alts_stp = self.__setup_logogram_alternatives(
            question_logogram,
            selected_logograms,
        )

        question = NgramSessionAssessmentQuestion.objects.create(
            number=question_num,
            question=self.__make_chr_2_rdcs_txt(question_logogram),
            expected_answer=alts_stp["correct_answer"],
            assessment=_assessment,
        )

        return PracticeQuestionSetup(
            question=question,
            alternatives=alts_stp["alternatives"],
        )

    def __select_logograms(self, session: NgramSession) -> Sequence[Logogram]:
        avlbl_logograms = list(
            Logogram.objects.filter(
                **{  # noqa: PIE804
                    "logogram_words__word__word_ngrams__ngram__"
                    "ngram_sessions__session__user": session.user,
                },
            ),
        )

        return cast("Sequence[Logogram]", random.sample(avlbl_logograms, k=5))

    def __make_chr_2_rdcs_txt(self, logogram: Logogram) -> str:
        return f"What radicals compose the character {logogram.id}?"

    def __setup_logogram_alternatives(
        self,
        question_logogram: Logogram,
        selected_logograms: Sequence[Logogram],
    ) -> AlternativesSetup:
        correct_answer = PracticeSessionAssessmentQuestionAnswer.A
        alt_letters = list(PracticeSessionAssessmentQuestionAnswer)
        alternatives: list[NgramSessionAssessmentQuestionAlt] = []
        lgg_rdcs_mapping = self.__make_lgg_rdcs_mapping(selected_logograms)

        for ltt_idx, curr_char in enumerate(selected_logograms):
            if curr_char == question_logogram:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                NgramSessionAssessmentQuestionAlt(
                    letter=alt_letters[ltt_idx],
                    type=PracticeAssessmentAlternativeTypeChoices.TEXT,
                    payload=" ".join(
                        radical.id for radical in lgg_rdcs_mapping[curr_char.id]
                    ),
                ),
            )

        return AlternativesSetup(
            correct_answer=correct_answer,
            alternatives=alternatives,
        )

    def __make_lgg_rdcs_mapping(
        self,
        logograms: Sequence[Logogram],
    ) -> dict[LogogramId, list[Radical]]:
        lgg_rdcs_pairs = RadicalLogogramMap.objects.filter(
            logogram__in=logograms,
        ).select_related("logogram", "radical")
        result: dict[LogogramId, list[Radical]] = defaultdict(list)

        for lgg_rdcs_pair in lgg_rdcs_pairs:
            result[lgg_rdcs_pair.logogram_id].append(lgg_rdcs_pair.radical)

        return result
