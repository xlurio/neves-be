from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.char_lm.serializers import LogogramSerializer
from neves_be.ngram_sessions.services import owned_ngram_session_ngram_or_404
from neves_be.ngram_sessions.services import owned_ngram_session_ngram_word_or_404
from neves_be.ngram_sessions.services import owned_ngram_session_word_logogram_or_404
from neves_be.practice_sessions.services.utils import make_session_getter
from neves_be.word_lm.serializers import NgramSerializer
from neves_be.word_lm.serializers import WordSerializer

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.ngram_sessions.types import NgramSessionId


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ngram_session_ngrams_view(
    request: Request,
    session_id: NgramSessionId,
    ngram_num: int,
) -> Response:
    getter = make_session_getter(request.user, "ngrams")
    session = getter.get_session(session_id)
    total_ngrams = session.session_ngrams.count()
    ngram = owned_ngram_session_ngram_or_404(session, ngram_num)

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-ngrams",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num + 1,
                },
            ),
        )
        if ngram_num < total_ngrams
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-ngrams",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num - 1,
                },
            ),
        )
        if ngram_num > 1
        else None
    )
    return Response(
        {
            "count": total_ngrams,
            "next": next_url,
            "previous": previous_url,
            "payload": NgramSerializer(ngram).data,
        },
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ngram_session_ngram_words_view(
    request: Request,
    session_id: NgramSessionId,
    ngram_num: int,
    word_num: int,
) -> Response:
    getter = make_session_getter(request.user, "ngrams")
    session = getter.get_session(session_id)
    ngram = owned_ngram_session_ngram_or_404(session, ngram_num)
    total_words = ngram.ngram_words.count()
    word = owned_ngram_session_ngram_word_or_404(ngram, word_num, total_words)

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-ngram-word",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num,
                    "word_num": word_num + 1,
                },
            ),
        )
        if word_num < total_words
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-ngram-word",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num,
                    "word_num": word_num - 1,
                },
            ),
        )
        if word_num > 1
        else None
    )
    return Response(
        {
            "count": total_words,
            "next": next_url,
            "previous": previous_url,
            "payload": WordSerializer(word).data,
        },
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ngram_session_word_logogram_view(
    request: Request,
    session_id: NgramSessionId,
    ngram_num: int,
    word_num: int,
    logogram_num: int,
) -> Response:
    getter = make_session_getter(request.user, "ngrams")
    session = getter.get_session(session_id)
    ngram = owned_ngram_session_ngram_or_404(session, ngram_num)
    total_words = ngram.ngram_words.count()
    word = owned_ngram_session_ngram_word_or_404(ngram, word_num, total_words)
    total_logograms = word.word_logograms.count()
    logogram = owned_ngram_session_word_logogram_or_404(
        word,
        logogram_num,
        total_logograms,
    )

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-word-logogram",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num,
                    "word_num": word_num,
                    "logogram_num": logogram_num + 1,
                },
            ),
        )
        if logogram_num < total_logograms
        else None
    )
    previous_url = (
        request.build_absolute_uri(
            reverse(
                "api-ngram-session-word-logogram",
                kwargs={
                    "session_id": str(session.pk),
                    "ngram_num": ngram_num,
                    "word_num": word_num,
                    "logogram_num": logogram_num - 1,
                },
            ),
        )
        if logogram_num > 1
        else None
    )
    return Response(
        {
            "count": total_logograms,
            "next": next_url,
            "previous": previous_url,
            "payload": LogogramSerializer(logogram).data,
        },
    )
