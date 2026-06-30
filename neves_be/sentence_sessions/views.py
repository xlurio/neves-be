from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.practice_sessions.views import DefaultPagination
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.serializers import SentenceSessionSerializer
from neves_be.sentence_sessions.services import create_sentence_session
from neves_be.sentence_sessions.services import owned_sentence_session_or_404

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.sentence_sessions.types import SentenceSessionId


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def sentence_sessions_view(request: Request) -> Response:
    if request.method == "GET":
        queryset = (
            SentenceSession.objects.filter(user=request.user)
            .annotate(
                num_of_sentences=models.Count("session_sentences"),
            )
            .order_by(
                "-created_at",
            )
        )
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)

        return paginator.get_paginated_response(
            SentenceSessionSerializer(page, many=True).data,
        )

    new_sentence_session = create_sentence_session(request)
    return Response(SentenceSessionSerializer(new_sentence_session).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_session_detail_view(
    request: Request,
    session_id: SentenceSessionId,
) -> Response:
    return Response(
        SentenceSessionSerializer(
            owned_sentence_session_or_404(request, session_id),
        ).data,
    )
