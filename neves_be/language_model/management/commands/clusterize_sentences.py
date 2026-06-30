from typing import TYPE_CHECKING

import numpy as np
from django.core.management.base import BaseCommand
from language_model.models import Sentence
from language_model.models import SentenceCluster
from language_model.models import Word
from language_model.models import WordSentenceMap
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

if TYPE_CHECKING:
    from django.db import models


class Command(BaseCommand):
    help = "Clusterize sentences by similarity"

    def handle(self, *args, **options) -> None:
        del args, options

        sentences = self.__get_sentences_qs().values_list("value", flat=True)

        preprocessing = make_pipeline(
            HashingVectorizer(),
            TruncatedSVD(n_components=100),
            Normalizer(copy=False),
        )

        cluster = MiniBatchKMeans()
        labels = cluster.fit_predict(preprocessing.fit_transform(sentences))
        _silhouette_score = silhouette_score(sentences, labels, sample_size=1e4)

        SentenceCluster.objects.bulk_create(
            SentenceCluster(id=label) for label in np.unique(labels)
        )

        sentences_to_update: list[Sentence] = []

        for idx, label in enumerate(labels):
            curr_sentence = self.__get_sentences_qs()[idx]
            curr_sentence.cluster_id = label
            sentences_to_update.append(curr_sentence)

        Sentence.objects.bulk_update(sentences_to_update)

        self.stdout.write(self.style.SUCCESS("Sentences successfully clustered"))
        self.stdout.write(f"silhouette_score={_silhouette_score}")

    def __get_sentences_qs(self) -> models.QuerySet[Sentence]:
        if cached_sentence := getattr(self, "__sentence", None):
            return cached_sentence

        most_common_word_ids = Word.objects.order_by("-occurrences")[:1000].values_list(
            "pk",
            flat=True,
        )
        most_common_sentence_ids = WordSentenceMap.objects.filter(
            word_id__in=most_common_word_ids,
        ).values_list("sentence_id", flat=True)

        result = Sentence.objects.filter(
            pk__in=most_common_sentence_ids,
        ).order_by("pk")
        setattr(self, "__sentence", result)

        return result
