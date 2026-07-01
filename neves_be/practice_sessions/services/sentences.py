import logging
from collections import defaultdict
from collections.abc import Sequence

from django.db import models
from django.db import transaction
from django.db.models import functions as dj_funcs

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.language_model.types import SentenceId
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.models import SentenceSessionSentence


class SentenceSessionFactory(BaseSessionFactory):
    MIN_WORDS_RATE = 0.9
    MAX_ITER = 10

    @transaction.atomic
    def make_session(self) -> ConcretePracticeSession:
        _logger = logging.getLogger(self.make_session.__name__)
        _logger.info("Creating sentences practice session")

        not_learned_words = Word.objects.exclude(
            word_sentences__sentence__sentence_sessions__in=self.__get_user_sessions(),
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
            self.__annotate_likelihood_n_word_count_to_sentence_qs(  # type: ignore[misc]
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

        cluster = maybe_sentence.cluster

        _logger.info("Chosen cluster %d", cluster.id)

        assert cluster

        words_w_known_rads = Word.objects.filter(
            **{  # noqa: PIE804
                "word_logograms__logogram__logogram_radicals__radical__"
                "radical_sessions__session__"
                "in": RadicalSession.objects.filter(
                    user=self._user,
                    highest_score__gte=70,
                ),
            },
        )

        most_likely_sequences_in_cluster_qs = (
            self.__annotate_likelihood_n_word_count_to_sentence_qs(
                cluster.sentences.get_queryset(),
            )
            .filter(sentence_words__word__in=words_w_known_rads)
            .order_by("-word_count", "-likelihood")
        )  # type: ignore[misc]

        session_sentences_to_create = []

        new_session = SentenceSession.objects.create(
            user=self._user,
            sentence_cluster=cluster,
        )

        cluster_words = set(
            Word.objects.filter(word_sentences__sentence__cluster=cluster),
        )
        session_words = set()
        sentence2word_mapping = self.__make_sentence_2_words_mapping(
            most_likely_sequences_in_cluster_qs,
        )
        curr_idx = 0

        while (
            len(cluster_words.intersection(session_words))
            <= len(cluster_words) * self.MIN_WORDS_RATE
            and curr_idx <= self.MAX_ITER
        ):
            curr_sentence = most_likely_sequences_in_cluster_qs[curr_idx]
            _logger.info("Appending '%s'", curr_sentence.value)

            session_words = session_words.union(sentence2word_mapping[curr_sentence.pk])

            session_sentences_to_create.append(
                SentenceSessionSentence(
                    session=new_session,
                    sentence=curr_sentence,
                    position=curr_idx + 1,
                ),
            )

            curr_idx += 1

        SentenceSessionSentence.objects.bulk_create(session_sentences_to_create)

        wrds_to_learn_percentage = len(cluster_words.intersection(session_words)) / len(
            cluster_words,
        )

        assert new_session.session_sentences.exists(), "No sentence was attached"
        assert wrds_to_learn_percentage >= self.MIN_WORDS_RATE, (
            f"{wrds_to_learn_percentage * 100}% learned"
        )

        return new_session

    def __get_user_sessions(self) -> models.QuerySet[SentenceSession]:
        return SentenceSession.objects.filter(user=self._user)

    def __make_sentence_2_words_mapping(
        self,
        sentences: Sequence[Sentence],
    ) -> dict[SentenceId, list[Word]]:
        _logger = logging.getLogger(self.__make_sentence_2_words_mapping.__name__)

        _logger.info("Making sentence-words mapping")

        word_sentence_pairs = WordSentenceMap.objects.filter(
            sentence__in=sentences,
        ).select_related("sentence", "word")
        result = defaultdict(list)

        for word_sentence_pair in word_sentence_pairs:
            result[word_sentence_pair.sentence_id].append(word_sentence_pair.word)

        return result

    def __annotate_likelihood_n_word_count_to_sentence_qs(
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
        return Word.objects.aggregate(
            occurrences_sum=models.Sum("occurrences"),
        )["occurrences_sum"]
