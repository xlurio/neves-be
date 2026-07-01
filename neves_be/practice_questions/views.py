from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.common.api import error_response
from neves_be.common.api import load_request_data
from neves_be.practice_assessments.constants import ANSWER_CHOICES
from neves_be.practice_assessments.serializers import PracticeQuestionSerializer
from neves_be.practice_assessments.services.assessments import make_assessment_getter

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assessments.types import AssessmentType
    from neves_be.practice_assessments.types import PracticeSessionAssessmentId


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def practice_assessment_question_view(
    request: Request,
    assessment_type: AssessmentType,
    assessment_id: PracticeSessionAssessmentId,
    question_num: int,
) -> Response:
    getter = make_assessment_getter(request.user, assessment_type)
    assessment = getter.get_assessment(assessment_id)
    total_questions = assessment.questions.count()
    question = assessment.questions.filter(number=question_num).first()

    if question is None:
        msg = "Question not found for this test."
        raise Http404(msg)

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-practice-test-question",
                kwargs={
                    "assessment_id": str(assessment.id),
                    "question_num": question_num + 1,
                },
            ),
        )
        if question_num < total_questions
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-practice-test-question",
                kwargs={
                    "assessment_id": str(assessment.id),
                    "question_num": question_num - 1,
                },
            ),
        )
        if question_num > 1
        else None
    )
    return Response(
        {
            "count": total_questions,
            "next": next_url,
            "previous": previous_url,
            "id": str(assessment.id),
            "sessionId": assessment.session.pk,
            "payload": PracticeQuestionSerializer(question).data,
        },
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def practice_assessment_answer_view(
    request: Request,
    assessment_type: AssessmentType,
    assessment_id: PracticeSessionAssessmentId,
) -> Response:
    getter = make_assessment_getter(request.user, assessment_type)
    assessment = getter.get_assessment(assessment_id)
    data = load_request_data(request)

    try:
        question_num = int(str(data.get("questionNum", "")))
    except (TypeError, ValueError):
        return error_response(
            "INVALID_QUESTION",
            "Invalid question",
            "A valid question number is required.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    answer = str(data.get("answer", "")).lower()
    if answer not in ANSWER_CHOICES:
        return error_response(
            "INVALID_ANSWER",
            "Invalid answer",
            "Answer must be one of: a, b, c, d, e.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    question = assessment.questions.filter(number=question_num).first()
    if question is None:
        return error_response(
            "QUESTION_MISSED",
            "Question not found",
            "The requested question does not exist for this test.",
            http_status=status.HTTP_409_CONFLICT,
            payload={"questionMissed": question_num},
        )

    question.curr_answer = answer
    question.save(update_fields=["curr_answer"])
    return Response({"status": "ok"})
