from __future__ import annotations

from typing import NewType
from typing import TypedDict
from uuid import UUID

SessionId = NewType("SessionId", UUID)


class RadicalsStatistics(TypedDict):
    progress: float


class SentencesStatistics(TypedDict):
    is_unlocked: bool
    progress: float
