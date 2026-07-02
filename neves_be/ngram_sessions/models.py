from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from neves_be.practice_sessions.models import PracticeSession
from neves_be.practice_sessions.models import PracticeSessionItem
from neves_be.practice_sessions.models import PracticeSessionItemMeta
from neves_be.practice_sessions.models import PracticeSessionMeta

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.ngram_sessions.types import NgramSessionId
    from neves_be.practice_assessments.models import NgramSessionAssessment
    from neves_be.word_lm.models import Ngram
    from neves_be.word_lm.types import NgramId


class NgramSession(PracticeSession):
    session_ngrams: RelatedManager[NgramSessionNgram]
    assessments: RelatedManager[NgramSessionAssessment]

    class Meta(PracticeSessionMeta): ...


class NgramSessionNgram(PracticeSessionItem):
    session = models.ForeignKey(
        NgramSession,
        on_delete=models.CASCADE,
        related_name="session_ngrams",
    )
    session_id: NgramSessionId
    ngram: models.ForeignKey[Ngram, Ngram] = models.ForeignKey(
        "word_lm.Ngram",
        on_delete=models.CASCADE,
        related_name="ngram_sessions",
    )
    ngram_id: NgramId

    class Meta(PracticeSessionItemMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["session", "ngram"],
                name="uniq_session_ngram",
            ),
            models.UniqueConstraint(
                fields=["session", "position"],
                name="uniq_ngram_session_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.position}:{self.ngram_id}"
