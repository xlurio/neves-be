from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from neves_be.char_lm.models import Logogram

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.ngram_sessions.models import NgramSessionNgram
    from neves_be.word_lm.types import LogogramId
    from neves_be.word_lm.types import NgramId
    from neves_be.word_lm.types import SentenceId
    from neves_be.word_lm.types import WordId


class Word(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.TextField()
    pronounce: models.CharField[str, str] = models.CharField(max_length=512, blank=True)
    pos_tag = models.CharField(max_length=255)
    occurrences = models.PositiveIntegerField()
    word_logograms: RelatedManager[LogogramWordMap]
    word_ngrams: RelatedManager[WordNgramMap]
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
    word_id: WordId
    logogram = models.ForeignKey(Logogram, on_delete=models.CASCADE)
    logogram_id: LogogramId

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["word", "logogram"],
                name="uniq_word_logogram",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.word_id}:{self.logogram_id}"


class Sentence(models.Model):
    id: models.IntegerField[int, SentenceId] = models.IntegerField(primary_key=True)
    value: models.TextField[str, str] = models.TextField()
    sentence_ngrams: RelatedManager[NgramSentenceMap]
    sentence_words: RelatedManager[WordSentenceMap]

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


class Ngram(models.Model):
    id: models.IntegerField[int, NgramId] = models.IntegerField(primary_key=True)
    value: models.TextField[str, str] = models.TextField()
    n_words = models.PositiveIntegerField()
    occurrences = models.PositiveIntegerField()
    ngram_words: RelatedManager[WordNgramMap]
    ngram_sentences: RelatedManager[NgramSentenceMap]
    ngram_sessions: RelatedManager[NgramSessionNgram]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.value


class WordNgramMap(models.Model):
    ngram = models.ForeignKey(
        Ngram,
        on_delete=models.CASCADE,
        related_name="ngram_words",
    )
    ngram_id: NgramId
    word = models.ForeignKey(
        "word_lm.Word",
        on_delete=models.CASCADE,
        related_name="word_ngrams",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ngram", "word"],
                name="uniq_ngram_word",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ngram_id}:{self.word_id}"


class NgramSentenceMap(models.Model):
    ngram = models.ForeignKey(
        Ngram,
        on_delete=models.CASCADE,
        related_name="ngram_sentences",
    )
    ngram_id: NgramId
    sentence = models.ForeignKey(
        "word_lm.Sentence",
        on_delete=models.CASCADE,
        related_name="sentence_ngrams",
    )
    sentence_id: SentenceId

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ngram", "sentence"],
                name="uniq_ngram_sentence",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ngram_id}:{self.sentence_id}"
