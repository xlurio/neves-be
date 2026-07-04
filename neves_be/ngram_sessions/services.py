from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import Http404

from neves_be.word_lm.models import Logogram
from neves_be.word_lm.models import Ngram
from neves_be.word_lm.models import Word

if TYPE_CHECKING:
    from neves_be.ngram_sessions.models import NgramSession


def owned_ngram_session_ngram_or_404(
    session: NgramSession,
    ngram_num: int,
) -> Ngram:
    ngrams_qs = Ngram.objects.filter(
        id__in=session.session_ngrams.values("ngram_id"),
        ngram_sessions__position=ngram_num,
    ).order_by("-occurrences")

    ngram = ngrams_qs.filter(ngram_sessions__position=ngram_num).first()

    if ngram is None:
        msg = "Ngram not found for this session."
        raise Http404(msg)

    return ngram


def owned_ngram_session_ngram_word_or_404(
    ngram: Ngram,
    word_num: int,
    total_words: int,
) -> Word:
    if word_num > total_words:
        msg = "Word not found for this ngram session."
        raise Http404(msg)

    return ngram.ngram_words.order_by("word__occurrences")[word_num - 1].word


def owned_ngram_session_word_logogram_or_404(
    word: Word,
    logogram_num: int,
    total_logograms: int,
) -> Logogram:
    if logogram_num > total_logograms:
        msg = "Word not found for this ngram session."
        raise Http404(msg)

    return word.word_logograms.order_by("logogram__occurrences")[
        logogram_num - 1
    ].logogram
