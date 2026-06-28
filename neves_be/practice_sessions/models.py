from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class PracticeSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    highest_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        abstract = True

    def __str__(self) -> str:
        return str(self.id)
