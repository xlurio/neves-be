from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


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
            models.UniqueConstraint(fields=["logogram", "radical"], name="uniq_logogram_radical"),
        ]


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
            models.UniqueConstraint(fields=["word", "logogram"], name="uniq_word_logogram"),
        ]


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
            models.UniqueConstraint(fields=["sentence", "word"], name="uniq_sentence_word"),
        ]


class RadicalSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    num_of_radicals = models.PositiveIntegerField(default=0)
    highest_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]


class RadicalSessionRadical(models.Model):
    session = models.ForeignKey(RadicalSession, on_delete=models.CASCADE, related_name="session_radicals")
    radical = models.ForeignKey(Radical, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["session", "position"]
        constraints = [
            models.UniqueConstraint(fields=["session", "radical"], name="uniq_session_radical"),
            models.UniqueConstraint(fields=["session", "position"], name="uniq_session_position"),
        ]


class RadicalSessionTest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(RadicalSession, on_delete=models.CASCADE, related_name="tests")
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-finished_at", "id"]


class RadicalSessionTestQuestion(models.Model):
    class Type(models.TextChoices):
        AUDIO_TO_LOGOGRAM = "AUDIO-TO-LOGOGRAM", _("Audio to Logogram")
        LOGOGRAM_TO_AUDIO = "LOGOGRAM-TO-AUDIO", _("Logogram to Audio")
        LOGOGRAM_TO_MEANING = "LOGOGRAM-TO-MEANING", _("Logogram to Meaning")
        LOGOGRAM_TO_PINYIN = "LOGOGRAM-TO-PINYIN", _("Logogram to Pinyin")
        MEANING_TO_LOGOGRAM = "MEANING-TO-LOGOGRAM", _("Meaning to Logogram")
        PINYIN_TO_LOGOGRAM = "PINYIN-TO-LOGOGRAM", _("Pinyin to Logogram")

    class Answer(models.TextChoices):
        A = "a", "A"
        B = "b", "B"
        C = "c", "C"
        D = "d", "D"
        E = "e", "E"

    test = models.ForeignKey(RadicalSessionTest, on_delete=models.CASCADE, related_name="questions")
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=32, choices=Type.choices)
    question = models.TextField()
    alternatives = models.JSONField(default=list)
    audio = models.CharField(max_length=512, blank=True, default="")
    curr_answer = models.CharField(max_length=1, choices=Answer.choices, null=True, blank=True)
    expected_answer = models.CharField(max_length=1, choices=Answer.choices)

    class Meta:
        ordering = ["test", "number"]
        constraints = [
            models.UniqueConstraint(fields=["test", "number"], name="uniq_test_question_number"),
        ]
