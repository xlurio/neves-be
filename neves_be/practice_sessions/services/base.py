import abc

from django.db import models
from django.http import Http404
from rest_framework.request import Request

from neves_be.ngram_sessions.models import NgramSession
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.practice_sessions.types import ConcretePracticeSessionId
from neves_be.radical_sessions.models import RadicalSession
from neves_be.users.models import User


class BasePracticeSessionAccessor:
    SESSION_TYPE: type[ConcretePracticeSession]
    NOT_FOUND_MSG: str
    ITEMS_RELATED_NAME: str
    TOTAL_ITEMS_FIELD: str

    def __init__(self, user: User) -> None:
        self.__user = user

    def get_sessions(self) -> models.QuerySet[ConcretePracticeSession]:
        return self.SESSION_TYPE.objects.annotate(
            **{
                self.TOTAL_ITEMS_FIELD: models.Count(self.ITEMS_RELATED_NAME),
            },
        ).filter(user=self.__user)

    def get_session(
        self,
        session_id: ConcretePracticeSessionId,
    ) -> ConcretePracticeSession:
        session = self.get_sessions().filter(id=session_id).first()

        if session is None:
            raise Http404(self.NOT_FOUND_MSG)
        return session


class RadicalSessionAccessor(BasePracticeSessionAccessor):
    SESSION_TYPE = RadicalSession
    NOT_FOUND_MSG = "Radical session not found."
    ITEMS_RELATED_NAME = "session_radicals"
    TOTAL_ITEMS_FIELD = "num_of_radicals"


class NgramSessionAccessor(BasePracticeSessionAccessor):
    SESSION_TYPE = NgramSession
    NOT_FOUND_MSG = "Ngram session not found."
    ITEMS_RELATED_NAME = "session_ngrams"
    TOTAL_ITEMS_FIELD = "num_of_ngrams"


class BaseSessionFactory(abc.ABC):
    def __init__(self, user: User) -> None:
        self._user = user

    @abc.abstractmethod
    def make_session(self) -> ConcretePracticeSession: ...

    @property
    def user(self) -> Request:
        return self._user
