from typing import NewType
from typing import TypedDict
from uuid import UUID

NgramSessionId = NewType("NgramSessionId", UUID)


class NgramsStatistics(TypedDict):
    is_unlocked: bool
    progress: float
