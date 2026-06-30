from typing import TYPE_CHECKING
from typing import assert_never

from django.db import models
from django.http import Http404

from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession

if TYPE_CHECKING:
    from neves_be.practice_sessions.types import ConcretePracticeSession
    from neves_be.practice_sessions.types import ConcretePracticeSessionId
    from neves_be.practice_sessions.types import SessionType
    from neves_be.users.models import User


class BasePracticeSessionAccessor:
    SESSION_TYPE: type[ConcretePracticeSession]
    NOT_FOUND_MSG: str
    ITEMS_RELATED_NAME: str

    def __init__(self, user: User) -> None:
        self.__user = user

    def get_session(
        self,
        session_id: ConcretePracticeSessionId,
    ) -> ConcretePracticeSession:
        session = (
            self.SESSION_TYPE.objects.annotate(
                total_items=models.Count(self.ITEMS_RELATED_NAME),
            )
            .filter(id=session_id, user=self.__user)
            .first()
        )
        if session is None:
            raise Http404(self.NOT_FOUND_MSG)
        return session


class RadicalSessionAccessor(BasePracticeSessionAccessor):
    SESSION_TYPE = RadicalSession
    NOT_FOUND_MSG = "Radical session not found."
    ITEMS_RELATED_NAME = "session_radicals"


class SentenceSessionAccessor(BasePracticeSessionAccessor):
    SESSION_TYPE = SentenceSession
    NOT_FOUND_MSG = "Sentence session not found."
    ITEMS_RELATED_NAME = "session_radicals"


def make_session_getter(
    user: User,
    session_type: SessionType,
) -> BasePracticeSessionAccessor:
    if session_type == "radicals":
        return RadicalSessionAccessor(user)

    if session_type == "sentences":
        return SentenceSessionAccessor(user)

    assert_never(session_type)
