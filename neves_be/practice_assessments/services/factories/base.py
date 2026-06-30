from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_assessments.types import ConcretePracticeSessionAssessment
    from neves_be.practice_sessions.types import ConcretePracticeSession


class BaseAssessmentFactory(abc.ABC):
    def __init__(self, request: Request) -> None:
        self.__request = request

    @abc.abstractmethod
    def make_assessment(
        self,
        session: ConcretePracticeSession,
    ) -> ConcretePracticeSessionAssessment: ...

    @property
    def request(self) -> Request:
        return self.__request
