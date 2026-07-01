from typing import cast

from neves_be.practice_assessments.types import AnswerChoice
from neves_be.practice_assessments.types import RadicalAssessmentQuestionType
from neves_be.practice_questions.models import RadicalSessionAssessmentQuestion

ANSWER_CHOICES: tuple[AnswerChoice, ...] = ("a", "b", "c", "d", "e")
MINIMUM_ASSESSMENT_POOL_SIZE = len(ANSWER_CHOICES)
ASSESSMENT_QUESTION_COUNT = 10

RADICAL_QUESTION_TYPES: tuple[RadicalAssessmentQuestionType, ...] = (
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.AUDIO_TO_LOGOGRAM,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_AUDIO,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_MEANING,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.LOGOGRAM_TO_PINYIN,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.MEANING_TO_LOGOGRAM,
    ),
    cast(
        "RadicalAssessmentQuestionType",
        RadicalSessionAssessmentQuestion.Type.PINYIN_TO_LOGOGRAM,
    ),
)

MASK_TOKEN = "[HIDDEN]"  # noqa: S105
