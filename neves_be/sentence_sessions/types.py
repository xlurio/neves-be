from typing import NewType
from typing import TypedDict
from uuid import UUID

SentenceSessionId = NewType("SentenceSessionId", UUID)


class SentencesStatistics(TypedDict):
    is_unlocked: bool
    progress: float
