from __future__ import annotations

from typing import NewType
from typing import TypedDict
from uuid import UUID

RadicalSessionId = NewType("RadicalSessionId", UUID)


class RadicalsStatistics(TypedDict):
    progress: float
