import logging

from django.db import models
from django.db import transaction
from django.db.models import functions as dj_funcs

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.practice_sessions.exceptions import CreateSentenceSessionError
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.models import SentenceSessionSentence
from neves_be.users.models import User


class SentenceSessionFactory(BaseSessionFactory):
    MIN_SENTENCES = 10
    MAX_ITER = MIN_SENTENCES

    def __init__(self, user: User):
        super().__init__(user)
        self.__cache = {}

    @transaction.atomic
    def make_session(self) -> ConcretePracticeSession:
        _logger = logging.getLogger(self.make_session.__name__)
        _logger.info("Creating sentences practice session")

        if self.get_session_sentences_qs().count() <= self.MIN_SENTENCES:
            raise CreateSentenceSessionError(
                code="NOT_ENOUGH_RADICALS",
                title="Failed to create new session",
                details="Learn more radicals to proceed",
            )

        session_sentences_to_create = []

        new_session = SentenceSession.objects.create(user=self._user)

        for sentence_idx, curr_sentence in enumerate(
            self.get_session_sentences_qs()[:10],
        ):
            _logger.info("Appending '%s'", curr_sentence.value)

            session_sentences_to_create.append(
                SentenceSessionSentence(
                    session=new_session,
                    sentence=curr_sentence,
                    position=sentence_idx + 1,
                ),
            )

        SentenceSessionSentence.objects.bulk_create(session_sentences_to_create)

        assert new_session.session_sentences.exists(), "No sentence was attached"

        return new_session

    def get_session_sentences_qs(self) -> models.QuerySet[Sentence]:
        if cached := self.__cache.get(self.get_session_sentences_qs.__name__):
            return cached

        not_learned_words = Word.objects.exclude(
            **{  # noqa: PIE804
                "word_sentences__sentence__sentence_sessions__session__"
                "in": self.__get_user_sessions(),
            },
        ).annotate(
            likelihood=dj_funcs.Cast(
                models.F("occurrences"),
                output_field=models.FloatField(),
            )
            / dj_funcs.Cast(
                self.__get_total_occurrences(),
                output_field=models.FloatField(),
            ),
        )

        maybe_sentence = (
            self.__annotate_likelihood_to_sentence_qs(  # type: ignore[misc]
                Sentence.objects.filter(sentence_words__word__in=not_learned_words),
            )
            .order_by("-likelihood")
            .first()
        )

        if not maybe_sentence:
            raise PracticeSessionCreationError(
                code="NOT_ENOUGH_RADICALS",
                title="Not enough radicals",
                details="Learn more radicals before continuing to practice sentences.",
            )

        words_w_known_rads = Word.objects.filter(
            pk__in=maybe_sentence.sentence_words.values_list("word_id", flat=True),
            **{  # noqa: PIE804
                "word_logograms__logogram__logogram_radicals__radical__"
                "radical_sessions__session__"
                "in": RadicalSession.objects.filter(
                    user=self._user,
                    highest_score__gte=70,
                ),
            },
        )

        self.__cache[self.get_session_sentences_qs.__name__] = (
            self.__annotate_likelihood_to_sentence_qs(
                Sentence.objects.filter(
                    sentence_words__word__in=words_w_known_rads,
                ).exclude(sentence_sessions__session__in=self.__get_user_sessions()),
            ).order_by("-likelihood")
        )  # type: ignore[misc]

        return self.__cache[self.get_session_sentences_qs.__name__]

    def __get_user_sessions(self) -> models.QuerySet[SentenceSession]:
        return SentenceSession.objects.filter(user=self._user)

    def __annotate_likelihood_to_sentence_qs(
        self,
        sentence_qs: models.QuerySet[Sentence],
    ) -> models.QuerySet[Sentence]:
        total_occurrences = Word.objects.aggregate(
            occurrences_sum=models.Sum("occurrences"),
        )["occurrences_sum"]

        return sentence_qs.annotate(
            likelihood=models.Sum(
                dj_funcs.Ln(
                    dj_funcs.Cast(
                        models.F("sentence_words__word__occurrences"),
                        output_field=models.FloatField(),
                    )
                    / models.Value(
                        float(total_occurrences),
                        output_field=models.FloatField(),
                    ),
                ),
            ),
        )

    def __get_total_occurrences(self) -> int:
        if cached := self.__cache.get(self.__get_total_occurrences.__name__):
            return cached

        self.__cache[self.__get_total_occurrences.__name__] = Word.objects.aggregate(
            occurrences_sum=models.Sum("occurrences"),
        )["occurrences_sum"]

        return self.__cache[self.__get_total_occurrences.__name__]
