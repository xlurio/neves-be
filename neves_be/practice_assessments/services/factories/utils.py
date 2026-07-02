from typing import assert_never

from rest_framework.request import Request

from neves_be.practice_assessments.services.factories.base import BaseAssessmentFactory
from neves_be.practice_assessments.services.factories.ngrams import (
    NgramAssessmentFactory,
)
from neves_be.practice_assessments.services.factories.radicals import (
    RadicalAssessmentFactory,
)
from neves_be.practice_assessments.types import AssessmentType


def make_assessment_factory(
    request: Request,
    session_type: AssessmentType,
) -> BaseAssessmentFactory:
    if session_type == "radicals":
        return RadicalAssessmentFactory(request)

    if session_type == "ngrams":
        return NgramAssessmentFactory(request)

    assert_never(session_type)
