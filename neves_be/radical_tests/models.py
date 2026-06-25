from __future__ import annotations

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from neves_be.radical_sessions.models import RadicalSession


class RadicalSessionTest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        RadicalSession,
        on_delete=models.CASCADE,
        related_name="tests",
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-finished_at", "id"]

    def __str__(self) -> str:
        return str(self.id)


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

    test = models.ForeignKey(
        RadicalSessionTest,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=32, choices=Type.choices)
    question = models.TextField()
    alternatives = models.JSONField(default=list)
    audio = models.CharField(max_length=512, blank=True, default="")
    curr_answer = models.CharField(
        max_length=1,
        choices=Answer.choices,
        blank=True,
        default="",
    )
    expected_answer = models.CharField(max_length=1, choices=Answer.choices)

    class Meta:
        ordering = ["test", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "number"],
                name="uniq_test_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.test_id}:{self.number}"
