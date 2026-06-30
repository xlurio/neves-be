from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.http import Http404

from neves_be.language_model.models import Logogram
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word

if TYPE_CHECKING:
    from neves_be.sentence_sessions.models import SentenceSession


def owned_sentence_session_sentence_or_404(
    session: SentenceSession,
    sentence_num: int,
) -> Sentence:
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

    sentence = sentences_qs.filter(sentence_sessions__position=sentence_num).first()

    if sentence is None:
        msg = "Sentence not found for this session."
        raise Http404(msg)

    return sentence


def owned_sentence_session_sentence_word_or_404(
    sentence: Sentence,
    word_num: int,
    total_words: int,
) -> Word:
    if word_num > total_words:
        msg = "Word not found for this sentence session."
        raise Http404(msg)

    return sentence.sentence_words.order_by("word__occurrences")[word_num].word


def owned_sentence_session_word_logogram_or_404(
    word: Word,
    logogram_num: int,
    total_logograms: int,
) -> Logogram:
    if logogram_num > total_logograms:
        msg = "Word not found for this sentence session."
        raise Http404(msg)

    return word.word_logograms.order_by("logogram__occurrences")[logogram_num].logogram
