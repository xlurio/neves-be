from typing import TYPE_CHECKING
from typing import assert_never

from neves_be.language_model.models import SentenceCluster
from neves_be.practice_sessions.serializers import RadicalSessionSerializer
from neves_be.practice_sessions.serializers import SentenceSessionSerializer
from neves_be.practice_sessions.services.base import BasePracticeSessionAccessor
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.services.base import RadicalSessionAccessor
from neves_be.practice_sessions.services.base import SentenceSessionAccessor
from neves_be.practice_sessions.services.radicals import RadicalSessionFactory
from neves_be.practice_sessions.services.sentences import SentenceSessionFactory
from neves_be.radical_sessions.models import RadicalSession

if TYPE_CHECKING:
    from urllib.request import Request

    from rest_framework import serializers

    from neves_be.practice_sessions.types import SessionType
    from neves_be.sentence_sessions.types import SentencesStatistics
    from neves_be.users.models import User


def make_session_getter(
    user: User,
    session_type: SessionType,
) -> BasePracticeSessionAccessor:
    if session_type == "radicals":
        return RadicalSessionAccessor(user)

    if session_type == "sentences":
        return SentenceSessionAccessor(user)

    assert_never(session_type)


def make_session_serializer(
    user: User,
    session_type: SessionType,
) -> type[serializers.Serializer]:
    if session_type == "radicals":
        return RadicalSessionSerializer(user)

    if session_type == "sentences":
        return SentenceSessionSerializer(user)

    assert_never(session_type)


def make_session_factory(session_type: SessionType, user: User) -> BaseSessionFactory:
    if session_type == "radicals":
        return RadicalSessionFactory(user)

    if session_type == "sentences":
        return SentenceSessionFactory(user)

    assert_never(session_type)


def make_sentences_stats(request: Request) -> SentencesStatistics:
    return {
        "is_unlocked": RadicalSession.objects.filter(
            user=request.user,
            highest_score__gte=70,
        ).exists(),
        "progress": SentenceCluster.objects.filter(
            sentencecluster_sessions__session__highest_score__gte=70,  # type: ignore[misc,unused-ignore]
        ).count()
        / SentenceCluster.objects.all().count(),
    }
