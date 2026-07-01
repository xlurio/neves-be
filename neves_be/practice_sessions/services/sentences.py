from collections import defaultdict
from collections.abc import Sequence

from django.db import models
from django.db.models import functions as dj_funcs

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word
from neves_be.language_model.models import WordSentenceMap
from neves_be.language_model.types import SentenceId
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.models import SentenceSessionSentence


class SentenceSessionFactory(BaseSessionFactory):
    def make_assessment(self) -> ConcretePracticeSession:
        sentence_session_sentence_sqs = SentenceSessionSentence.objects.filter(
            sentence__cluster_id=models.OuterRef("cluster_id"),
            session__user=self._user,
        ).values("sentence_id")

        maybe_sentence = (
            self.__annotate_likelihood_to_sentence_qs(  # type: ignore[misc]
                Sentence.objects.exclude(
                    pk__in=models.Subquery(sentence_session_sentence_sqs),
                    cluster__sentencecluster_sessions__session_id__isnull=False,
                ),
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

        assert cluster

        most_likely_sequences_in_cluster_qs = self.__annotate_likelihood_to_sentence_qs(
            cluster.sentences.get_queryset(),
        ).order_by("-likelihood")  # type: ignore[misc]

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
        MAX_ITER = 20  # noqa: N806

        while (
            len(cluster_words.intersection(session_words)) > len(cluster_words) * 0.9
            or curr_idx < MAX_ITER
        ):
            curr_sentence = most_likely_sequences_in_cluster_qs[curr_idx]
            session_words.union(sentence2word_mapping[curr_sentence.pk])

            session_sentences_to_create.append(
                SentenceSessionSentence(
                    session=new_session,
                    sentence=curr_sentence,
                    position=curr_idx + 1,
                ),
            )

        SentenceSessionSentence.objects.bulk_create(session_sentences_to_create)

        return new_session

    def __make_sentence_2_words_mapping(
        self,
        sentences: Sequence[Sentence],
    ) -> dict[SentenceId, list[Word]]:
        word_sentence_pairs = WordSentenceMap.objects.filter(sentence__in=sentences)
        result = defaultdict(list)

        for word_sentence_pair in word_sentence_pairs:
            result[word_sentence_pair.sentence_id].append(word_sentence_pair.word)

        return result

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
