from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.http import Http404
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.language_model.models import Sentence
from neves_be.language_model.serializers import SentenceSerializer
from neves_be.practice_sessions.views import DefaultPagination
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.serializers import SentenceSessionSerializer
from neves_be.sentence_sessions.services import create_sentence_session
from neves_be.sentence_sessions.services import owned_sentence_session_or_404

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.language_model.types import SentenceId
    from neves_be.radical_sessions.types import SessionId


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
def sentence_session_detail_view(request: Request, session_id: SessionId) -> Response:
    return Response(
        SentenceSessionSerializer(
            owned_sentence_session_or_404(request, session_id),
        ).data,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_session_sentences_view(
    request: Request,
    session_id: SessionId,
    sentence_num: SentenceId,
) -> Response:
    session = owned_sentence_session_or_404(request, session_id)

    total_sentences = session.session_sentences.count()
    sentences_qs = (
        Sentence.objects.filter(
            id__in=session.session_sentences.values("sentence_id"),
            sentence_sessions__position=sentence_num,
        )
        .annotate(
            occurrencies=models.Sum("sentence_words__word__occurrences"),
        )
        .order_by("-occurrencies")
    )

    sentence = sentences_qs.filter(sentence_sessions__position=sentence_num).first()  # type: ignore[misc,unused-ignore]

    if sentence is None:
        msg = "Sentence not found for this session."
        raise Http404(msg)

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-session-sentence",
                kwargs={
                    "session_id": str(session.pk),
                    "sentence_num": sentence_num + 1,
                },
            ),
        )
        if sentence_num < total_sentences
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-session-sentence",
                kwargs={
                    "session_id": str(session.pk),
                    "sentence_num": sentence_num - 1,
                },
            ),
        )
        if sentence_num > 1
        else None
    )
    return Response(
        {
            "count": total_sentences,
            "next": next_url,
            "previous": previous_url,
            "payload": SentenceSerializer(sentence).data,
        },
    )
