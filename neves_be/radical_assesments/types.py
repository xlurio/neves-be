from typing import TYPE_CHECKING
from typing import Literal
from typing import NewType
from typing import NotRequired
from typing import TypedDict
from uuid import UUID

if TYPE_CHECKING:
    from neves_be.practice_assesments.types import AlternativePayload
    from neves_be.practice_assesments.types import AnswerChoice
    from neves_be.practice_assesments.types import CurrentAnswer

RadicalSessionAssessmentId = NewType("RadicalSessionAssessmentId", UUID)

RadicalAssessmentQuestionType = Literal[
    "AUDIO-TO-LOGOGRAM",
    "LOGOGRAM-TO-AUDIO",
    "LOGOGRAM-TO-MEANING",
    "LOGOGRAM-TO-PINYIN",
    "MEANING-TO-LOGOGRAM",
    "PINYIN-TO-LOGOGRAM",
]


class RadicalAssessmentQuestionPayload(TypedDict):
    type: RadicalAssessmentQuestionType
    question: str
    alternatives: list[AlternativePayload]
    currAnswer: CurrentAnswer
    audio: NotRequired[str]


class ResultRadicalAssessmentQuestionPayload(TypedDict):
    type: RadicalAssessmentQuestionType
    question: str
    alternatives: list[AlternativePayload]
    currAnswer: AnswerChoice
    expectedAnswer: AnswerChoice
    audio: NotRequired[str]
