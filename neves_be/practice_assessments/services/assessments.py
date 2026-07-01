import abc
from typing import assert_never

from django.http import Http404
from rest_framework.request import Request

from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_assessments.models import SentenceSessionAssessment
from neves_be.practice_assessments.types import AssessmentType
from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
from neves_be.practice_assessments.types import PracticeSessionAssessmentId
from neves_be.users.models import User


class BaseAssessmentAccessor(abc.ABC):
    NOT_FOUND_ERROR_MSG: str
    ASSESSMENT_TYPE: type[ConcretePracticeSessionAssessment]

    def __init__(self, user: User) -> None:
        self.__user = user

    def get_assessment(
        self,
        assessment_id: PracticeSessionAssessmentId,
    ) -> ConcretePracticeSessionAssessment:
        assessment = (
            self.ASSESSMENT_TYPE.objects.select_related("session")
            .filter(
                id=assessment_id,
                session__user=self.__user,
            )
            .first()
        )

        if assessment is None:
            raise Http404(self.NOT_FOUND_ERROR_MSG)

        return assessment


class RadicalAssessmentAccessor(BaseAssessmentAccessor):
    NOT_FOUND_ERROR_MSG = "Radical test not found."
    ASSESSMENT_TYPE = RadicalSessionAssessment


class SentenceAssessmentAccessor(BaseAssessmentAccessor):
    NOT_FOUND_ERROR_MSG = "Sentence test not found."
    ASSESSMENT_TYPE = SentenceSessionAssessment


def make_assessment_getter(
    user: User,
    assessment_type: AssessmentType,
) -> BaseAssessmentAccessor:
    if assessment_type == "radicals":
        return RadicalAssessmentAccessor(user)

    if assessment_type == "sentences":
        return SentenceAssessmentAccessor(user)

    assert_never(assessment_type)


def safe_pronounce_url(request: Request, pronounce: str) -> str:
    if not pronounce:
        return ""
    if pronounce.startswith(("http://", "https://")):
        return pronounce
    if pronounce.startswith("/"):
        return request.build_absolute_uri(pronounce)
    return pronounce
