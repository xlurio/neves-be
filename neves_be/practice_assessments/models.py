from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.practice_assessments.types import RadicalSessionAssessmentId
    from neves_be.practice_assessments.types import SentenceSessionAssessmentId


class PracticeSessionAssessment(models.Model):
    id: models.UUIDField[uuid.UUID, uuid.UUID] = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    finished_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return str(self.id)


class PracticeSessionAssessmentQuestionAnswer(models.TextChoices):
    A = "a", "A"
    B = "b", "B"
    C = "c", "C"
    D = "d", "D"
    E = "e", "E"


class PracticeSessionAssessmentQuestion(models.Model):
    type = models.CharField()
    number = models.PositiveIntegerField()
    question = models.TextField()
    audio = models.CharField(max_length=512, blank=True, default="")
    curr_answer = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer.choices,
        blank=True,
        default="",
    )
    expected_answer = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer.choices,
    )
    question_alternatives: RelatedManager[PracticeSessionAssessmentQuestionAlt]

    class Meta:
        abstract = True


class PracticeAssessmentAlternativeTypeChoices(models.TextChoices):
    AUDIO = "AUDIO", "Audio"
    TEXT = "TEXT", "Text"


class PracticeSessionAssessmentQuestionAlt(models.Model):
    letter = models.CharField(
        max_length=1,
        choices=PracticeSessionAssessmentQuestionAnswer.choices,
    )
    type = models.CharField(
        max_length=255,
        choices=PracticeAssessmentAlternativeTypeChoices.choices,
    )
    payload = models.TextField()
    question = models.ForeignKey(
        PracticeSessionAssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="question_alternatives",
    )

    class Meta:
        ordering = ["question", "letter"]
        constraints = [
            models.UniqueConstraint(
                fields=["letter", "question"],
                name="uniq_letter_question",
            ),
        ]

    def __str__(self):
        return f"{self.type} alternative: {self.payload}"


class RadicalSessionAssessment(PracticeSessionAssessment):
    session: models.ForeignKey[RadicalSession, RadicalSession] = models.ForeignKey(
        RadicalSession,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
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
        ordering = ["assesment", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "number"],
                name="uniq_radical_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assesment_id}:{self.number}"


class SentenceSessionAssessment(PracticeSessionAssessment):
    session: models.ForeignKey[SentenceSession, SentenceSession] = models.ForeignKey(
        SentenceSession,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
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
        ordering = ["assessment", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["test", "number"],
                name="uniq_sentence_assessment_question_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assessment_id}:{self.number}"


class MaskedSentenceAudio(models.Model):
    id = models.IntegerField(primary_key=True)
    audio = models.FileField()

    def __str__(self) -> str:
        return f"masked sentence audio {self.id}: {self.audio.path}"


type ConcretePracticeSessionAssessmentQuestion = (
    RadicalSessionAssessmentQuestion | SentenceSessionAssessmentQuestion
)
