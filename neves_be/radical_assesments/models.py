from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from neves_be.practice_assesments.models import PracticeSessionAssessment
from neves_be.practice_assesments.models import PracticeSessionAssessmentQuestion

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.radical_assesments.types import RadicalSessionAssessmentId


class RadicalSessionAssessment(PracticeSessionAssessment):
    questions: RelatedManager[RadicalSessionAssessmentQuestion]

    class Meta:
        ordering = ["-finished_at", "id"]


class RadicalSessionAssessmentQuestion(PracticeSessionAssessmentQuestion):
    class Type(models.TextChoices):
        AUDIO_TO_LOGOGRAM = "AUDIO-TO-LOGOGRAM", _("Audio to Logogram")
        LOGOGRAM_TO_AUDIO = "LOGOGRAM-TO-AUDIO", _("Logogram to Audio")
        LOGOGRAM_TO_MEANING = "LOGOGRAM-TO-MEANING", _("Logogram to Meaning")
        LOGOGRAM_TO_PINYIN = "LOGOGRAM-TO-PINYIN", _("Logogram to Pinyin")
        MEANING_TO_LOGOGRAM = "MEANING-TO-LOGOGRAM", _("Meaning to Logogram")
        PINYIN_TO_LOGOGRAM = "PINYIN-TO-LOGOGRAM", _("Pinyin to Logogram")

    type = models.CharField(max_length=32, choices=Type.choices)
    assesment = models.ForeignKey(
        RadicalSessionAssessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    assesment_id: RadicalSessionAssessmentId

    class Meta:
        ordering = ["test", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "number"],
                name="uniq_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assesment_id}:{self.number}"
