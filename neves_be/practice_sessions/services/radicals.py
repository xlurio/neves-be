from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.models import RadicalSession


class RadicalSessionFactory(BaseSessionFactory):
    def make_assessment(self) -> ConcretePracticeSession:
        return RadicalSession.objects.create(user=self._user)
