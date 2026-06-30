from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.language_model.types import LogogramId
    from neves_be.language_model.types import SentenceClusterId
    from neves_be.language_model.types import SentenceId
    from neves_be.radical_sessions.models import RadicalSessionRadical
    from neves_be.sentence_sessions.models import SentenceSessionSentence


class Radical(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    pinyin = models.TextField()
    meaning = models.TextField()
    pronounce: models.CharField[str, str] = models.CharField(max_length=512)
    radical_sessions: RelatedManager[RadicalSessionRadical]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class Logogram(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    occurrences = models.PositiveIntegerField(default=0)
    pinyin = models.TextField(blank=True, default="")
    meaning = models.TextField(blank=True, default="")
    pronounce: models.CharField[str, str] = models.CharField(max_length=512)
    logogram_radicals: RelatedManager[RadicalLogogramMap]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class RadicalLogogramMap(models.Model):
    logogram = models.ForeignKey(
        Logogram,
        on_delete=models.CASCADE,
        related_name="logogram_radicals",
    )
    logogram_id: LogogramId
    radical = models.ForeignKey(
        Radical,
        on_delete=models.CASCADE,
        related_name="radical_logograms",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["logogram", "radical"],
                name="uniq_logogram_radical",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.logogram_id}:{self.radical_id}"


class Word(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.TextField(blank=True, default="")
    pronounce: models.CharField[str, str] = models.CharField(max_length=512)
    pos_tag = models.CharField(max_length=255, blank=True, default="")
    occurrences = models.PositiveIntegerField(default=0)
    word_logograms: RelatedManager[LogogramWordMap]
    word_sentences: RelatedManager[WordSentenceMap]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.value


class LogogramWordMap(models.Model):
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="word_logograms",
    )
    logogram = models.ForeignKey(Logogram, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["word", "logogram"],
                name="uniq_word_logogram",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.word_id}:{self.logogram_id}"


class SentenceCluster(models.Model):
    id = models.IntegerField(primary_key=True)
    sentences: RelatedManager[Sentence]
    sentencecluster_sessions: RelatedManager[SentenceSessionSentence]

    def __str__(self) -> str:
        if maybe_sentence := self.sentences.order_by("id").first():
            return maybe_sentence.value[:50]

        return str(self.pk)


class Sentence(models.Model):
    id: models.IntegerField[int, SentenceId] = models.IntegerField(primary_key=True)
    value: models.TextField[str, str] = models.TextField()
    cluster: models.ForeignKey[SentenceCluster, SentenceCluster | None] = (
        models.ForeignKey(
            SentenceCluster,
            on_delete=models.SET_NULL,
            related_name="sentences",
            null=True,
            default=None,
        )
    )
    cluster_id: SentenceClusterId
    sentence_words: RelatedManager[WordSentenceMap]
    sentence_sessions: RelatedManager[SentenceSessionSentence]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.value[:50]


class WordSentenceMap(models.Model):
    sentence = models.ForeignKey(
        Sentence,
        on_delete=models.CASCADE,
        related_name="sentence_words",
    )
    sentence_id: SentenceId
    word: models.ForeignKey[Word, Word] = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="word_sentences",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sentence", "word"],
                name="uniq_sentence_word",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sentence_id}:{self.word_id}"
