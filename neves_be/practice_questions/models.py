from __future__ import annotations

from typing import TYPE_CHECKING
from typing import NewType

from django.db import models
from django.utils.translation import gettext_lazy as _

from neves_be.common.models import UUIDPkModelMixin
from neves_be.practice_assessments.models import NgramSessionAssessment
from neves_be.practice_assessments.models import PracticeSessionAssessment
from neves_be.practice_assessments.models import RadicalSessionAssessment

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.practice_assessments.types import NgramSessionAssessmentId
    from neves_be.practice_assessments.types import RadicalSessionAssessmentId


class PracticeSessionAssessmentQuestionAnswer(models.TextChoices):
    A = "a", "A"
    B = "b", "B"
    C = "c", "C"
    D = "d", "D"
    E = "e", "E"


class PracticeSessionAssessmentQuestion(UUIDPkModelMixin, models.Model):
    type = models.CharField()
    number = models.PositiveIntegerField()
    question = models.TextField()
    audio = models.CharField(max_length=512, blank=True, default="")
    curr_answer = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer,
        blank=True,
        default="",
    )
    expected_answer = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer,
    )
    question_alternatives: RelatedManager[PracticeSessionAssessmentQuestionAlt]
    assessment: PracticeSessionAssessment
    assessment_id: RadicalSessionAssessmentId

    class Meta:
        abstract = True


PracticeSessionAssessmentQuestionId = NewType(
    "PracticeSessionAssessmentQuestionId",
    int,
)


class PracticeAssessmentAlternativeTypeChoices(models.TextChoices):
    AUDIO = "AUDIO", "Audio"
    TEXT = "TEXT", "Text"


class PracticeSessionAssessmentQuestionAlt(UUIDPkModelMixin, models.Model):
    letter = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer,
    )
    type = models.CharField(
        max_length=255,
        choices=PracticeAssessmentAlternativeTypeChoices,
    )
    payload = models.TextField()
    question: PracticeSessionAssessmentQuestion
    question_id: PracticeSessionAssessmentQuestionId

    class Meta:
        abstract = True
        ordering = ["question", "letter"]

    def __str__(self):
        return f"{self.type} alternative: {self.payload}"


class RadicalSessionAssessmentQuestion(PracticeSessionAssessmentQuestion):
    class Type(models.TextChoices):
        AUDIO_TO_LOGOGRAM = "AUDIO-TO-LOGOGRAM", _("Audio to Logogram")
        LOGOGRAM_TO_AUDIO = "LOGOGRAM-TO-AUDIO", _("Logogram to Audio")
        LOGOGRAM_TO_MEANING = "LOGOGRAM-TO-MEANING", _("Logogram to Meaning")
        LOGOGRAM_TO_PINYIN = "LOGOGRAM-TO-PINYIN", _("Logogram to Pinyin")
        MEANING_TO_LOGOGRAM = "MEANING-TO-LOGOGRAM", _("Meaning to Logogram")
        PINYIN_TO_LOGOGRAM = "PINYIN-TO-LOGOGRAM", _("Pinyin to Logogram")

    type = models.CharField(max_length=32, choices=Type.choices)
    assessment = models.ForeignKey(
        RadicalSessionAssessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    assessment_id: RadicalSessionAssessmentId

    class Meta:
        ordering = ["assessment", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "number"],
                name="uniq_radical_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assessment_id}:{self.number}"


class RadicalSessionAssessmentQuestionAlt(PracticeSessionAssessmentQuestionAlt):
    question = models.ForeignKey(
        RadicalSessionAssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="question_alternatives",
    )

    class Meta(PracticeSessionAssessmentQuestionAlt.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(
                fields=["letter", "question"],
                name="radical_uniq_letter_question",
            ),
        ]


class NgramSessionQuestionType(models.TextChoices):
    NGRAM_AUDIO_TO_WORD_AUDIO = (
        "NGRAM-AUDIO-TO-WORD-AUDIO",
        _("Ngram Audio to Word Audio"),
    )
    NGRAM_TEXT_TO_WORD_AUDIO = (
        "NGRAM-TEXT-TO-WORD-AUDIO",
        _("Ngram Text to Word Audio"),
    )
    NGRAM_AUDIO_TO_WORD_TEXT = (
        "NGRAM-AUDIO-TO-WORD-TEXT",
        _("Ngram Audio to Word Text"),
    )
    NGRAM_TEXT_TO_WORD_TEXT = (
        "NGRAM-TEXT-TO-WORD-TEXT",
        _("Ngram Text to Word Text"),
    )
    LOGOGRAM_TO_RADICALS = "LOGOGRAM-TO-RADICALS", _("Logogram to Radicals")


class NgramSessionAssessmentQuestion(PracticeSessionAssessmentQuestion):
    assessment = models.ForeignKey(
        NgramSessionAssessment,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    assessment_id: NgramSessionAssessmentId
    type = models.CharField(max_length=32, choices=NgramSessionQuestionType)

    class Meta:
        ordering = ["assessment", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "number"],
                name="uniq_ngram_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assessment_id}:{self.number}"


class NgramSessionAssessmentQuestionAlt(PracticeSessionAssessmentQuestionAlt):
    question = models.ForeignKey(
        NgramSessionAssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="question_alternatives",
    )

    class Meta(PracticeSessionAssessmentQuestionAlt.Meta):
        abstract = False
        constraints = [
            models.UniqueConstraint(
                fields=["letter", "question"],
                name="ngram_uniq_letter_question",
            ),
        ]


type ConcretePracticeSessionAssessmentQuestion = (
    RadicalSessionAssessmentQuestion | NgramSessionAssessmentQuestion
)
