from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.common.api import error_response
from neves_be.common.api import load_request_data
from neves_be.practice_assessments.constants import ANSWER_CHOICES
from neves_be.practice_assessments.serializers import PracticeQuestionResultSerializer
from neves_be.practice_assessments.serializers import PracticeQuestionSerializer
from neves_be.practice_assessments.serializers import make_practice_assessment_srlr_cls
from neves_be.practice_assessments.services.assessments import make_assessment_factory
from neves_be.practice_assessments.services.assessments import make_assessment_getter
from neves_be.practice_sessions.services import make_session_getter
from neves_be.practice_sessions.views import DefaultPagination

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assessments.types import AssessmentType
    from neves_be.practice_assessments.types import PracticeSessionAssessmentId
    from neves_be.practice_sessions.types import ConcretePracticeSessionId
    from neves_be.practice_sessions.types import SessionType


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
    except TypeError, ValueError:
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def practice_assessment_finish_view(
    request: Request,
    assessment_type: AssessmentType,
    assessment_id: PracticeSessionAssessmentId,
) -> Response:
    getter = make_assessment_getter(request.user, assessment_type)
    assessment = getter.get_assessment(assessment_id)
    unanswered_question = (
        assessment.questions.filter(curr_answer="").order_by("number").first()
    )

    if unanswered_question is not None:
        return error_response(
            "QUESTION_MISSED",
            "Question was missed",
            "At least one question has not been answered.",
            http_status=status.HTTP_409_CONFLICT,
            payload={"questionMissed": unanswered_question.number},
        )

    total_questions = assessment.questions.count()
    correct_answers = assessment.questions.filter(
        curr_answer=models.F("expected_answer"),
    ).count()
    assessment.score = (
        round((correct_answers / total_questions) * 100) if total_questions else 0
    )
    assessment.finished_at = timezone.now()
    assessment.save(update_fields=["score", "finished_at"])
    if assessment.score > assessment.session.highest_score:
        assessment.session.highest_score = assessment.score
        assessment.session.save(update_fields=["highest_score"])
    return Response({"status": "ok"})


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
                "api-radical-test-question",
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
                "api-radical-test-question",
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def practice_assessment_result_view(
    request: Request,
    assessment_type: AssessmentType,
    assessment_id: PracticeSessionAssessmentId,
) -> Response:
    getter = make_assessment_getter(request.user, assessment_type)
    assessment = getter.get_assessment(assessment_id)

    if not assessment.finished_at:
        return error_response(
            "UNFINISHED_ASSESSMENT",
            "Assessment not finished",
            "This test is yet to be finished and has no result.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "id": str(assessment.id),
            "sessionId": assessment.session.pk,
            "score": assessment.score,
            "questions": PracticeQuestionResultSerializer(
                assessment.questions.all(),
                many=True,
            ).data,
        },
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def practice_session_assessments_view(
    request: Request,
    session_type: SessionType,
    session_id: ConcretePracticeSessionId,
) -> Response:
    getter = make_session_getter(request.user, session_type)
    session = getter.get_session(session_id)
    serializer_cls = make_practice_assessment_srlr_cls(session_type)

    if request.method == "GET":
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(
            session.assessments.order_by("-finished_at", "id"),
            request,
        )

        return paginator.get_paginated_response(
            serializer_cls(page, many=True).data,
        )

    assessment_factory = make_assessment_factory(request, session_type)

    return Response(
        serializer_cls(
            assessment_factory.make_assessment(session),
        ).data,
        status=status.HTTP_201_CREATED,
    )
