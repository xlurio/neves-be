from django.db import transaction

from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.types import ConcretePracticeSession
from neves_be.radical_sessions.models import RadicalSession


class RadicalSessionFactory(BaseSessionFactory):
    @transaction.atomic
    def make_session(self) -> ConcretePracticeSession:
        return RadicalSession.objects.create(user=self._user)
