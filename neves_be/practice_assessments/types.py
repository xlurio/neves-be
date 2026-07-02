from __future__ import annotations

from typing import Literal
from typing import NewType
from uuid import UUID

from neves_be.practice_assessments.models import NgramSessionAssessment
from neves_be.practice_assessments.models import RadicalSessionAssessment

RadicalSessionAssessmentId = NewType("RadicalSessionAssessmentId", UUID)

type RadicalAssessmentQuestionType = Literal[
    "AUDIO-TO-LOGOGRAM",
    "LOGOGRAM-TO-AUDIO",
    "LOGOGRAM-TO-MEANING",
    "LOGOGRAM-TO-PINYIN",
    "MEANING-TO-LOGOGRAM",
    "PINYIN-TO-LOGOGRAM",
]


NgramSessionAssessmentId = NewType("NgramSessionAssessmentId", UUID)

type NgramAssessmentQuestionType = Literal[
    "NGRAM-AUDIO-TO-WORD-AUDIO",
    "NGRAM-TEXT-TO-WORD-AUDIO",
    "NGRAM-AUDIO-TO-WORD-TEXT",
    "NGRAM-TEXT-TO-WORD-TEXT",
    "LOGOGRAM-TO-RADICALS",
]


type PracticeSessionAssessmentId = RadicalSessionAssessmentId | NgramSessionAssessmentId
type ConcretePracticeSessionAssessment = (
    RadicalSessionAssessment | NgramSessionAssessment
)

type AssessmentType = Literal["radicals", "ngrams"]

type AnswerChoice = Literal["a", "b", "c", "d", "e"]
type CurrentAnswer = AnswerChoice | Literal[""]


type ConcretePracticeAssessmentQuestionType = (
    RadicalAssessmentQuestionType | NgramAssessmentQuestionType
)


type ConcreteAssessmentQuestionType = (
    RadicalAssessmentQuestionType | NgramAssessmentQuestionType
)
