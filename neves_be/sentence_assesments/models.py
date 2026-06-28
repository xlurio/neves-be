from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from neves_be.practice_assesments.models import PracticeSessionAssessment
from neves_be.practice_assesments.models import PracticeSessionAssessmentQuestion

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.sentence_assesments.types import SentenceSessionAssessmentId


class SentenceSessionAssessment(PracticeSessionAssessment):
    questions: RelatedManager[SentenceSessionAssessmentQuestion]

    class Meta:
        ordering = ["-finished_at", "id"]


class SentenceSessionAssessmentQuestion(PracticeSessionAssessmentQuestion):
    class Type(models.TextChoices):
        SENTENCE_AUDIO_TO_WORD_AUDIO = (
            "SENTENCE-AUDIO-TO-WORD-AUDIO",
            _("Sentence Audio to Word Audio"),
        )
        SENTENCE_TEXT_TO_WORD_AUDIO = (
            "SENTENCE-TEXT-TO-WORD-AUDIO",
            _("Sentence Text to Word Audio"),
        )
        SENTENCE_AUDIO_TO_WORD_TEXT = (
            "SENTENCE-AUDIO-TO-WORD-TEXT",
            _("Sentence Audio to Word Text"),
        )
        SENTENCE_TEXT_TO_WORD_TEXT = (
            "SENTENCE-TEXT-TO-WORD-TEXT",
            _("Sentence Text to Word Text"),
        )
        LOGOGRAM_TO_RADICALS = "LOGOGRAM-TO-RADICALS", _("Logogram to Radicals")

    assessment = models.ForeignKey(
        SentenceSessionAssessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    assessment_id: SentenceSessionAssessmentId
    type = models.CharField(max_length=32, choices=Type.choices)

    class Meta:
        ordering = ["test", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "number"],
                name="uniq_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assessment_id}:{self.number}"
