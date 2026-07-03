from typing import NewType
from typing import TypedDict
from uuid import UUID

NgramSessionId = NewType("NgramSessionId", UUID)


class NgramsStatistics(TypedDict):
    isUnlocked: bool
    progress: float
