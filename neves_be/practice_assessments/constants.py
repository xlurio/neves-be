from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neves_be.practice_assessments.types import AnswerChoice

ANSWER_CHOICES: tuple[AnswerChoice, ...] = ("a", "b", "c", "d", "e")
MINIMUM_ASSESSMENT_POOL_SIZE = len(ANSWER_CHOICES)
ASSESSMENT_QUESTION_COUNT = 10
