import abc
from collections.abc import Sequence
from typing import TypedDict

from neves_be.practice_assessments.models import PracticeSessionAssessment
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestion
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAlt
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAnswer


class PracticeQuestionSetup(TypedDict):
    question: PracticeSessionAssessmentQuestion
    alternatives: Sequence[PracticeSessionAssessmentQuestionAlt]


class AlternativesSetup(TypedDict):
    correct_answer: PracticeSessionAssessmentQuestionAnswer
    alternatives: Sequence[PracticeSessionAssessmentQuestionAlt]


class BasePracticeQuestionFactory:
    def make_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        stp = self._setup_question(assessment, question_num)
        return self._annotate_question_to_alts_stp(
            question=stp["question"],
            alternatives=stp["alternatives"],
        )

    @abc.abstractmethod
    def _setup_question(
        self,
        assessment: PracticeSessionAssessment,
        question_num: int,
    ) -> PracticeQuestionSetup:
        del assessment, question_num

    def _annotate_question_to_alts_stp(
        self,
        question: PracticeSessionAssessmentQuestion,
        alternatives: Sequence[PracticeSessionAssessmentQuestionAlt],
    ) -> PracticeQuestionSetup:
        alternatives_to_create: list[PracticeSessionAssessmentQuestionAlt] = []

        for alt in alternatives:
            alt.question = question
            alternatives_to_create.append(alt)

        return PracticeQuestionSetup(
            question=question,
            alternatives=alternatives_to_create,
        )
