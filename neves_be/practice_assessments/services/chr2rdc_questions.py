import random
from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import Radical
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.types import LogogramId
from neves_be.practice_assessments.models import PracticeSessionAssessment
from neves_be.practice_assessments.services.questions import AlternativesSetup
from neves_be.practice_assessments.services.questions import BasePracticeQuestionFactory
from neves_be.practice_assessments.services.questions import PracticeQuestionSetup
from neves_be.practice_questions.models import PracticeAssessmentAlternativeTypeChoices
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestion
from neves_be.practice_questions.models import SentenceSessionAssessmentQuestionAlt
from neves_be.sentence_sessions.models import SentenceSession


class Char2RadicalQuestionFactory(BasePracticeQuestionFactory):
    def _setup_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        selected_logograms = self.__select_logograms(assessment.session)
        question_logogram = selected_logograms[random.randint(0, 4)]
        alts_stp = self.__setup_logogram_alternatives(
            question_logogram,
            selected_logograms,
        )

        question = SentenceSessionAssessmentQuestion.objects.create(
            number=question_num,
            question=self.__make_chr_2_rdcs_txt(question_logogram),
            expected_answer=alts_stp["correct_answer"],
            assessment=assessment,
        )

        return PracticeQuestionSetup(
            question=question,
            alternatives=alts_stp["alternatives"],
        )

    def __select_logograms(self, session: SentenceSession) -> Sequence[Logogram]:
        avlbl_logograms = list(
            Logogram.objects.filter(
                **{  # noqa: PIE804
                    "logogram_words__word__word_sentences__sentence__"
                    "sentence_sessions__session__user": session.user,
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
        alternatives: list[SentenceSessionAssessmentQuestionAlt] = []
        lgg_rdcs_mapping = self.__make_lgg_rdcs_mapping(selected_logograms)

        for ltt_idx, curr_char in enumerate(selected_logograms):
            if curr_char == question_logogram:
                correct_answer = alt_letters[ltt_idx]

            alternatives.append(
                SentenceSessionAssessmentQuestionAlt(
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
        lgg_rdcs_pairs = RadicalLogogramMap.objects.filter(logogram__in=logograms)
        result: dict[LogogramId, list[Radical]] = defaultdict(list)

        for lgg_rdcs_pair in lgg_rdcs_pairs:
            result[lgg_rdcs_pair.logogram_id].append(lgg_rdcs_pair.radical)

        return result
