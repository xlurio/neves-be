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
from neves_be.practice_sessions.views import DefaultPagination
from neves_be.sentence_assesments.serializers import SentenceSessionAssessmentSerializer
from neves_be.sentence_assesments.services import ANSWER_CHOICES
from neves_be.sentence_assesments.services import create_session_assessment
from neves_be.sentence_assesments.services import owned_assessment_or_404
from neves_be.sentence_assesments.services import serialize_question_payload
from neves_be.sentence_assesments.services import serialize_result_questions
from neves_be.sentence_sessions.services import owned_sentence_session_or_404

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assesments.types import AssessmentId
    from neves_be.radical_sessions.types import SessionId


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def sentence_session_assessments_view(request: Request, session_id: SessionId) -> Response:
    session = owned_sentence_session_or_404(request, session_id)
    if request.method == "GET":
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(
            session.tests.order_by("-finished_at", "id"),
            request,
        )
        return paginator.get_paginated_response(
            SentenceSessionAssessmentSerializer(page, many=True).data,
        )

    try:
        test = create_session_assessment(session, request)
    except ValueError:
        return error_response(
            "NOT_ENOUGH_RADICALS",
            "Could not create test",
            "At least five sentences are required to generate a test.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        SentenceSessionAssessmentSerializer(test).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_assessment_question_view(
    request: Request,
    assessment_id: AssessmentId,
    question_num: int,
) -> Response:
    test = owned_assessment_or_404(request, assessment_id)
    total_questions = test.questions.count()
    question = test.questions.filter(number=question_num).first()
    if question is None:
        msg = "Question not found for this test."
        raise Http404(msg)
    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-test-question",
                kwargs={"assessment_id": str(test.id), "question_num": question_num + 1},
            ),
        )
        if question_num < total_questions
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-test-question",
                kwargs={"assessment_id": str(test.id), "question_num": question_num - 1},
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
            "id": str(test.id),
            "sentencesSessionId": test.session.pk,
            "payload": serialize_question_payload(question, request),
        },
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sentence_assessment_answer_view(request: Request, assessment_id: AssessmentId) -> Response:
    test = owned_assessment_or_404(request, assessment_id)
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

    question = test.questions.filter(number=question_num).first()
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
def sentence_assessment_finish_view(request: Request, assessment_id: AssessmentId) -> Response:
    test = owned_assessment_or_404(request, assessment_id)
    unanswered_question = (
        test.questions.filter(curr_answer="").order_by("number").first()
    )
    if unanswered_question is not None:
        return error_response(
            "QUESTION_MISSED",
            "Question was missed",
            "At least one question has not been answered.",
            http_status=status.HTTP_409_CONFLICT,
            payload={"questionMissed": unanswered_question.number},
        )

    total_questions = test.questions.count()
    correct_answers = test.questions.filter(
        curr_answer=models.F("expected_answer"),
    ).count()
    test.score = (
        round((correct_answers / total_questions) * 100) if total_questions else 0
    )
    test.finished_at = timezone.now()
    test.save(update_fields=["score", "finished_at"])
    if test.score > test.session.highest_score:
        test.session.highest_score = test.score
        test.session.save(update_fields=["highest_score"])
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_assessment_result_view(request: Request, assessment_id: AssessmentId) -> Response:
    test = owned_assessment_or_404(request, assessment_id)

    if not test.finished_at:
        return error_response(
            "UNFINISHED_ASSESSMENT",
            "Assessment not finished",
            "This test is yet to be finished and has no result.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "id": str(test.id),
            "sentencesSessionId": test.session.pk,
            "score": test.score,
            "questions": serialize_result_questions(test, request),
        },
    )
