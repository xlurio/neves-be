from __future__ import annotations

from typing import Literal
from typing import NewType
from typing import NotRequired
from typing import TypedDict
from uuid import UUID

TestId = NewType("TestId", UUID)

QuestionType = Literal[
    "AUDIO-TO-LOGOGRAM",
    "LOGOGRAM-TO-AUDIO",
    "LOGOGRAM-TO-MEANING",
    "LOGOGRAM-TO-PINYIN",
    "MEANING-TO-LOGOGRAM",
    "PINYIN-TO-LOGOGRAM",
]

AnswerChoice = Literal["a", "b", "c", "d", "e"]
CurrentAnswer = AnswerChoice | Literal[""]
AlternativeType = Literal["AUDIO", "TEXT"]


class AlternativePayload(TypedDict):
    type: AlternativeType
    payload: str


class QuestionPayload(TypedDict):
    type: QuestionType
    question: str
    alternatives: list[AlternativePayload]
    currAnswer: CurrentAnswer
    audio: NotRequired[str]


class ResultQuestionPayload(TypedDict):
    type: QuestionType
    question: str
    alternatives: list[AlternativePayload]
    currAnswer: AnswerChoice
    expectedAnswer: AnswerChoice
    audio: NotRequired[str]
