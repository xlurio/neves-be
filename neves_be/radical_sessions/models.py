from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from neves_be.language_model.models import Radical
from neves_be.practice_sessions.models import PracticeSession
from neves_be.practice_sessions.models import PracticeSessionItem
from neves_be.practice_sessions.models import PracticeSessionItemMeta
from neves_be.practice_sessions.models import PracticeSessionMeta

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.radical_assessments.models import RadicalSessionAssessment

    class Meta:
        ordering = ["-created_at"]


class RadicalSession(PracticeSession):
    session_radicals: RelatedManager[RadicalSessionRadical]
    assessments: RelatedManager[RadicalSessionAssessment]

    class Meta(PracticeSessionMeta): ...


class RadicalSessionRadical(PracticeSessionItem):
    session = models.ForeignKey(
        RadicalSession,
        on_delete=models.CASCADE,
        related_name="session_radicals",
    )
    radical = models.ForeignKey(
        Radical,
        on_delete=models.CASCADE,
        related_name="radical_sessions",
    )

    class Meta(PracticeSessionItemMeta):
        constraints = [
            models.UniqueConstraint(
                fields=["session", "radical"],
                name="uniq_session_radical",
            ),
            models.UniqueConstraint(
                fields=["session", "position"],
                name="uniq_radical_session_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.position}:{self.radical_id}"
