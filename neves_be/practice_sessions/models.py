from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from neves_be.common.models import UUIDPkModel

if TYPE_CHECKING:
    from neves_be.users.models import User


class PracticeSession(UUIDPkModel):
    user: models.ForeignKey[User, User | None] = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    highest_score = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return str(self.id)


class PracticeSessionMeta:
    ordering = ("-created_at",)


class PracticeSessionItem(UUIDPkModel):
    position = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class PracticeSessionItemMeta:
    ordering = ["session", "position"]
