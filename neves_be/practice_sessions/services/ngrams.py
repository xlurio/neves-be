from __future__ import annotations

import itertools
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from django.db import models
from django.db import transaction

from neves_be.common.exceptions import AsyncOperationError
from neves_be.genai.services.text2speech import generate_speech
from neves_be.ngram_sessions.models import NgramSession
from neves_be.ngram_sessions.models import NgramSessionNgram
from neves_be.ngram_sessions.models import NgramSessionRequest
from neves_be.practice_sessions.exceptions import CreateNgramSessionError
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.radical_sessions.models import RadicalSession
from neves_be.word_lm.models import LogogramWordMap
from neves_be.word_lm.models import Ngram
from neves_be.word_lm.models import Word
from neves_be.word_lm.models import WordNgramMap

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence

    from neves_be.char_lm.models import Logogram
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.users.models import User
    from neves_be.word_lm.types import NgramId
    from neves_be.word_lm.types import WordId


class NgramSessionFactory(BaseSessionFactory):
    MIN_NGRAMS = 10
    MAX_ITER = MIN_NGRAMS

    def __init__(self, user: User):
        super().__init__(user)
        self.__cache = {}

    def make_session(self) -> ConcretePracticeSession:
        from neves_be.ngram_sessions.tasks import async_create_ngram_session  # noqa: I001, PLC0415

        if NgramSessionRequest.objects.filter(
            user=self._user,
            finished_at__isnull=True,
        ).exists():
            raise CreateNgramSessionError(
                code="VALIDATION_ERROR",
                title="There is already an sequences session being created",
                details="As soon as it is ready it'll be available to you",
            )

        async_create_ngram_session.delay(self._user)

        raise AsyncOperationError(
            code="ASYNC_OP",
            title="Ngram creation is being processed",
            details="As soon as your session is ready we'll make it available to you",
        )

    @transaction.atomic
    def make_session_async(
        self,
        request: NgramSessionRequest,
    ) -> ConcretePracticeSession:
        _logger = logging.getLogger(self.make_session.__name__)
        _logger.info("Creating ngrams practice session")

        if self.get_session_ngrams_qs().count() <= self.MIN_NGRAMS:
            raise CreateNgramSessionError(
                code="NOT_ENOUGH_RADICALS",
                title="Failed to create new session",
                details="Learn more radicals to proceed",
            )

        new_session = NgramSession.objects.create(
            user=self._user,
            request=request,
        )

        NgramSessionNgram.objects.bulk_create(
            self.__make_session_ngrams_to_create(new_session),
        )

        assert new_session.session_ngrams.exists(), "No ngram was attached"

        return new_session

    def __make_session_ngrams_to_create(
        self,
        session: NgramSession,
    ) -> Sequence[NgramSessionNgram]:
        _logger = logging.getLogger(self.__make_session_ngrams_to_create.__name__)

        session_ngrams_to_create = []

        session_ngrams = self.get_session_ngrams_qs()[:10]
        ngrams_to_words = self.__make_ngram_to_words_mapping(session_ngrams)
        ngrams_to_logograms = self.__make_ngram_to_logograms_mapping(session_ngrams)

        with ThreadPoolExecutor(1) as executor:
            for ngram_idx, curr_ngram in enumerate(
                session_ngrams,
            ):
                _logger.info("Appending '%s'", curr_ngram.value)

                session_ngrams_to_create.append(
                    NgramSessionNgram(
                        session=session,
                        ngram=curr_ngram,
                        position=ngram_idx + 1,
                    ),
                )
                executor.submit(generate_speech, curr_ngram.value)
                executor.map(
                    generate_speech,
                    [word.value for word in ngrams_to_words[curr_ngram.pk]],
                )
                executor.map(
                    generate_speech,
                    [char.pk for char in ngrams_to_logograms[curr_ngram.pk]],
                )

        return session_ngrams_to_create

    def __make_ngram_to_logograms_mapping(
        self,
        ngrams: Sequence[Ngram],
    ) -> dict[NgramId, set[Logogram]]:
        _logger = logging.getLogger(self.__make_ngram_to_logograms_mapping.__name__)
        _logger.info("Making n-gram to logograms mappings")

        ngram_words = self.__make_ngram_to_words_mapping(ngrams)
        word_logograms = self.__make_word_to_logograms_mapping(
            itertools.chain(words for words in ngram_words.values()),
        )
        result: dict[NgramId, set[Logogram]] = defaultdict(set)

        for ngram_id, words in word_logograms.items():
            for word in words:
                result[ngram_id].union(word_logograms[word.pk])

        return result

    def __make_ngram_to_words_mapping(
        self,
        ngrams: Iterable[Ngram],
    ) -> dict[NgramId, set[Word]]:
        _logger = logging.getLogger(self.__make_ngram_to_words_mapping.__name__)
        _logger.info("Making n-gram to words mappings")

        pairs = WordNgramMap.objects.filter(ngram__in=ngrams).select_related(
            "pair",
            "word",
        )
        result: dict[NgramId, set[Word]] = defaultdict(set)

        for pair in pairs:
            result[pair.pk].add(pair.word)

        return result

    def __make_word_to_logograms_mapping(
        self,
        words: Iterable[Word],
    ) -> dict[WordId, set[Logogram]]:
        pairs = LogogramWordMap.objects.filter(word__in=words).select_related(
            "logogram",
            "word",
        )
        result: dict[WordId, set[Logogram]] = defaultdict(set)

        for pair in pairs:
            result[pair.word_id].add(pair.logogram)

        return result

    def get_session_ngrams_qs(self) -> models.QuerySet[Ngram]:
        if cached := self.__cache.get(self.get_session_ngrams_qs.__name__):
            return cached

        most_common_word_ids = Word.objects.order_by("-occurrences")[:1000].values_list(
            "pk",
            flat=True,
        )

        not_learned_words = Word.objects.filter(pk__in=most_common_word_ids).exclude(
            **{  # noqa: PIE804
                "word_ngrams__ngram__ngram_sessions__session__"
                "in": self.__get_user_sessions(),
            },
        )

        maybe_ngram = (
            Ngram.objects.filter(ngram_words__word__in=not_learned_words)
            .order_by("-occurrences")
            .first()
        )

        if not maybe_ngram:
            raise PracticeSessionCreationError(
                code="NOT_ENOUGH_RADICALS",
                title="Not enough radicals",
                details="Learn more radicals before continuing to practice ngrams.",
            )

        words_w_known_rads = Word.objects.filter(
            pk__in=maybe_ngram.ngram_words.values_list("word_id", flat=True),
            **{  # noqa: PIE804
                "word_logograms__logogram__logogram_radicals__radical__"
                "radical_sessions__session__"
                "in": RadicalSession.objects.filter(
                    user=self._user,
                    highest_score__gte=70,
                ),
            },
        )

        self.__cache[self.get_session_ngrams_qs.__name__] = (
            Ngram.objects.filter(
                ngram_words__word__in=words_w_known_rads,
            )
            .exclude(ngram_sessions__session__in=self.__get_user_sessions())
            .order_by("-occurrences", "-n_words")
        )  # type: ignore[misc]

        return self.__cache[self.get_session_ngrams_qs.__name__]

    def __get_user_sessions(self) -> models.QuerySet[NgramSession]:
        return NgramSession.objects.filter(user=self._user)

    def __get_total_occurrences(self) -> int:
        if cached := self.__cache.get(self.__get_total_occurrences.__name__):
            return cached

        self.__cache[self.__get_total_occurrences.__name__] = Word.objects.aggregate(
            occurrences_sum=models.Sum("occurrences"),
        )["occurrences_sum"]

        return self.__cache[self.__get_total_occurrences.__name__]
