from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.language_model.serializers import LogogramSerializer
from neves_be.language_model.serializers import SentenceSerializer
from neves_be.language_model.serializers import WordSerializer
from neves_be.sentence_session_sentences.services import (
    owned_sentence_session_sentence_or_404,
)
from neves_be.sentence_session_sentences.services import (
    owned_sentence_session_sentence_word_or_404,
)
from neves_be.sentence_session_sentences.services import (
    owned_sentence_session_word_logogram_or_404,
)
from neves_be.sentence_sessions.services import owned_sentence_session_or_404

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.sentence_sessions.types import SentenceSessionId


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_session_sentences_view(
    request: Request,
    session_id: SentenceSessionId,
    sentence_num: int,
) -> Response:
    session = owned_sentence_session_or_404(request, session_id)
    total_sentences = session.session_sentences.count()
    sentence = owned_sentence_session_sentence_or_404(session, sentence_num)

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sentence_session_sentence_words_view(
    request: Request,
    session_id: SentenceSessionId,
    sentence_num: int,
    word_num: int,
) -> Response:
    session = owned_sentence_session_or_404(request, session_id)
    sentence = owned_sentence_session_sentence_or_404(session, sentence_num)
    total_words = sentence.sentence_words.count()
    word = owned_sentence_session_sentence_word_or_404(sentence, word_num, total_words)

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-session-sentence-word",
                kwargs={
                    "session_id": str(sentence.pk),
                    "sentence_num": sentence_num,
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
                "api-sentence-session-sentence-word",
                kwargs={
                    "session_id": str(sentence.pk),
                    "sentence_num": sentence_num,
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
def sentence_session_word_logogram_view(
    request: Request,
    session_id: SentenceSessionId,
    sentence_num: int,
    word_num: int,
    logogram_num: int,
) -> Response:
    session = owned_sentence_session_or_404(request, session_id)
    sentence = owned_sentence_session_sentence_or_404(session, sentence_num)
    total_words = sentence.sentence_words.count()
    word = owned_sentence_session_sentence_word_or_404(sentence, word_num, total_words)
    total_logograms = word.word_logograms.count()
    logogram = owned_sentence_session_word_logogram_or_404(
        word,
        logogram_num,
        total_logograms,
    )

    next_url = (
        request.build_absolute_uri(
            reverse(
                "api-sentence-session-word-logogram",
                kwargs={
                    "session_id": str(sentence.pk),
                    "sentence_num": sentence_num,
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
                "api-sentence-session-word-logogram",
                kwargs={
                    "session_id": str(sentence.pk),
                    "sentence_num": sentence_num,
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
