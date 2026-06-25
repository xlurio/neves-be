from __future__ import annotations

from django.db import models


class Radical(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    pinyin = models.TextField(blank=True, default="")
    meaning = models.TextField(blank=True, default="")
    main_representation = models.PositiveIntegerField(null=True, blank=True)
    other_vars = models.JSONField(default=list, blank=True)
    pronounce = models.CharField(max_length=512, blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class Logogram(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    occurrences = models.PositiveIntegerField(default=0)
    pinyin = models.TextField(blank=True, default="")
    meaning = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class RadicalLogogramMap(models.Model):
    logogram = models.ForeignKey(Logogram, on_delete=models.CASCADE)
    radical = models.ForeignKey(Radical, on_delete=models.CASCADE)

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
    pos_tag = models.CharField(max_length=255, blank=True, default="")
    occurrences = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.value


class LogogramWordMap(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
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


class Sentence(models.Model):
    id = models.IntegerField(primary_key=True)
    value = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.value[:50]


class WordSentenceMap(models.Model):
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sentence", "word"],
                name="uniq_sentence_word",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sentence_id}:{self.word_id}"
