from typing import Literal

from neves_be.ngram_sessions.models import NgramSession
from neves_be.ngram_sessions.types import NgramSessionId
from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.types import RadicalSessionId

type ConcretePracticeSession = RadicalSession | NgramSession
type ConcretePracticeSessionId = RadicalSessionId | NgramSessionId
type SessionType = Literal["radicals", "ngrams"]
