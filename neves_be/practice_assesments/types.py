from __future__ import annotations

from typing import Literal
from typing import NewType
from typing import NotRequired
from typing import TypedDict
from uuid import UUID

AnswerChoice = Literal["a", "b", "c", "d", "e"]
CurrentAnswer = AnswerChoice | Literal[""]
AlternativeType = Literal["AUDIO", "TEXT"]


AssessmentId = NewType("AssessmentId", UUID)


class AlternativePayload(TypedDict):
    type: AlternativeType
    payload: str
