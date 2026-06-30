from typing import Literal

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.types import RadicalSessionId
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.types import SentenceSessionId

type ConcretePracticeSession = RadicalSession | SentenceSession
type ConcretePracticeSessionId = RadicalSessionId | SentenceSessionId
type SessionType = Literal["radicals", "sentences"]
