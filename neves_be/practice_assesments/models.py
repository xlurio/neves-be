from __future__ import annotations

import uuid

from django.db import models

from neves_be.radical_sessions.models import RadicalSession


class PracticeSessionAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session: models.ForeignKey[RadicalSession, RadicalSession] = models.ForeignKey(
        RadicalSession,
        on_delete=models.CASCADE,
        related_name="assesments",
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return str(self.id)


class PracticeSessionAssessmentQuestion(models.Model):
    class Answer(models.TextChoices):
        A = "a", "A"
        B = "b", "B"
        C = "c", "C"
        D = "d", "D"
        E = "e", "E"

    number = models.PositiveIntegerField()
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
        abstract = True
