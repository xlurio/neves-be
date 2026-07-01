from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db import models

from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.practice_questions.models import RadicalSessionAssessmentQuestion
    from neves_be.practice_questions.models import SentenceSessionAssessmentQuestion
    from neves_be.practice_sessions.models import PracticeSession


class PracticeSessionAssessment(models.Model):
    id: models.UUIDField[uuid.UUID, uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    session: PracticeSession

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return str(self.id)


class RadicalSessionAssessment(PracticeSessionAssessment):
    session: models.ForeignKey[RadicalSession, RadicalSession] = models.ForeignKey(
        RadicalSession,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    questions: RelatedManager[RadicalSessionAssessmentQuestion]

    class Meta:
        ordering = ["-finished_at", "id"]


class SentenceSessionAssessment(PracticeSessionAssessment):
    session: models.ForeignKey[SentenceSession, SentenceSession] = models.ForeignKey(
        SentenceSession,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    questions: RelatedManager[SentenceSessionAssessmentQuestion]

    class Meta:
        ordering = ["-finished_at", "id"]
