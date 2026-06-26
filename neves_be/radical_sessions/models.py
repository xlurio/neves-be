from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from neves_be.radicals.models import Radical

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager


class RadicalSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    highest_score = models.PositiveIntegerField(default=0)
    session_radicals: RelatedManager[RadicalSessionRadical]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.id)


class RadicalSessionRadical(models.Model):
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
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["session", "position"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "radical"],
                name="uniq_session_radical",
            ),
            models.UniqueConstraint(
                fields=["session", "position"],
                name="uniq_session_position",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.position}:{self.radical_id}"
