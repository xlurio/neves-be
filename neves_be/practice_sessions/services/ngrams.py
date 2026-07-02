import logging

from django.db import models
from django.db import transaction

from neves_be.ngram_sessions.models import NgramSession
from neves_be.ngram_sessions.models import NgramSessionNgram
from neves_be.practice_sessions.exceptions import CreateNgramSessionError
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.radical_sessions.models import RadicalSession
from neves_be.users.models import User
from neves_be.word_lm.models import Ngram
from neves_be.word_lm.models import Word


class NgramSessionFactory(BaseSessionFactory):
    MIN_NGRAMS = 10
    MAX_ITER = MIN_NGRAMS

    def __init__(self, user: User):
        super().__init__(user)
        self.__cache = {}

    @transaction.atomic
    def make_session(self) -> ConcretePracticeSession:
        _logger = logging.getLogger(self.make_session.__name__)
        _logger.info("Creating ngrams practice session")

        if self.get_session_ngrams_qs().count() <= self.MIN_NGRAMS:
            raise CreateNgramSessionError(
                code="NOT_ENOUGH_RADICALS",
                title="Failed to create new session",
                details="Learn more radicals to proceed",
            )

        session_ngrams_to_create = []

        new_session = NgramSession.objects.create(user=self._user)

        for ngram_idx, curr_ngram in enumerate(
            self.get_session_ngrams_qs()[:10],
        ):
            _logger.info("Appending '%s'", curr_ngram.value)

            session_ngrams_to_create.append(
                NgramSessionNgram(
                    session=new_session,
                    ngram=curr_ngram,
                    position=ngram_idx + 1,
                ),
            )

        NgramSessionNgram.objects.bulk_create(session_ngrams_to_create)

        assert new_session.session_ngrams.exists(), "No ngram was attached"

        return new_session

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
