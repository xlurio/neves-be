from __future__ import annotations

from typing import Literal
from typing import NewType
from uuid import UUID

from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_assessments.models import SentenceSessionAssessment

RadicalSessionAssessmentId = NewType("RadicalSessionAssessmentId", UUID)

type RadicalAssessmentQuestionType = Literal[
    "AUDIO-TO-LOGOGRAM",
    "LOGOGRAM-TO-AUDIO",
    "LOGOGRAM-TO-MEANING",
    "LOGOGRAM-TO-PINYIN",
    "MEANING-TO-LOGOGRAM",
    "PINYIN-TO-LOGOGRAM",
]


SentenceSessionAssessmentId = NewType("SentenceSessionAssessmentId", UUID)

type SentenceAssessmentQuestionType = Literal[
    "SENTENCE-AUDIO-TO-WORD-AUDIO",
    "SENTENCE-TEXT-TO-WORD-AUDIO",
    "SENTENCE-AUDIO-TO-WORD-TEXT",
    "SENTENCE-TEXT-TO-WORD-TEXT",
    "LOGOGRAM-TO-RADICALS",
]


type PracticeSessionAssessmentId = (
    RadicalSessionAssessmentId | SentenceSessionAssessmentId
)
type ConcretePracticeSessionAssessment = (
    RadicalSessionAssessment | SentenceSessionAssessment
)

type AssessmentType = Literal["radicals", "sentences"]

type AnswerChoice = Literal["a", "b", "c", "d", "e"]
type CurrentAnswer = AnswerChoice | Literal[""]


type ConcretePracticeAssessmentQuestionType = (
    RadicalAssessmentQuestionType | SentenceAssessmentQuestionType
)


type ConcreteAssessmentQuestionType = (
    RadicalAssessmentQuestionType | SentenceAssessmentQuestionType
)
