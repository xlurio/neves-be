from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import SentenceCluster
from neves_be.practice_sessions.models import PracticeSession

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.language_model.types import SentenceId
    from neves_be.sentence_sessions.types import SentenceSessionId


class SentenceSession(PracticeSession):
    session_sentences: RelatedManager[SentenceSessionSentence]

    class Meta:
        ordering = ["-created_at"]


class SentenceSessionSentence(models.Model):
    session = models.ForeignKey(
        SentenceSession,
        on_delete=models.CASCADE,
        related_name="session_sentences",
    )
    session_id: SentenceSessionId
    sentence = models.ForeignKey(
        Sentence,
        on_delete=models.CASCADE,
        related_name="sentence_sessions",
    )
    sentence_id: SentenceId
    sentence_cluster = models.ForeignKey(
        SentenceCluster,
        on_delete=models.CASCADE,
        related_name="sentencecluster_sessions",
    )
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["session", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "sentence"],
                name="uniq_session_sentence",
            ),
            models.UniqueConstraint(
                fields=["session", "sentence_cluster"],
                name="uniq_session_sentence_cluster",
            ),
            models.UniqueConstraint(
                fields=["session", "position"],
                name="uniq_seq_session_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.position}:{self.sentence_id}"
