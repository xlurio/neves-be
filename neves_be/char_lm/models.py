from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from neves_be.radical_sessions.models import RadicalSessionRadical
    from neves_be.word_lm.types import LogogramId


class Radical(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    pinyin = models.TextField()
    meaning = models.TextField()
    pronounce: models.CharField[str, str] = models.CharField(max_length=512)
    radical_sessions: RelatedManager[RadicalSessionRadical]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class Logogram(models.Model):
    id = models.CharField(max_length=4, primary_key=True)
    occurrences = models.PositiveIntegerField(default=0)
    pinyin = models.TextField()
    meaning = models.TextField()
    pronounce: models.CharField[str, str] = models.CharField(max_length=512, blank=True)
    logogram_radicals: RelatedManager[RadicalLogogramMap]

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.id


class RadicalLogogramMap(models.Model):
    logogram = models.ForeignKey(
        Logogram,
        on_delete=models.CASCADE,
        related_name="logogram_radicals",
    )
    logogram_id: LogogramId
    radical = models.ForeignKey(
        Radical,
        on_delete=models.CASCADE,
        related_name="radical_logograms",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["logogram", "radical"],
                name="uniq_logogram_radical",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.logogram_id}:{self.radical_id}"
