from typing import assert_never

from rest_framework import serializers
from rest_framework.request import Request

from neves_be.ngram_sessions.models import NgramSession
from neves_be.ngram_sessions.types import NgramsStatistics
from neves_be.practice_sessions.serializers import NgramSessionSerializer
from neves_be.practice_sessions.serializers import RadicalSessionSerializer
from neves_be.practice_sessions.services.base import BasePracticeSessionAccessor
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.services.base import NgramSessionAccessor
from neves_be.practice_sessions.services.base import RadicalSessionAccessor
from neves_be.practice_sessions.services.ngrams import NgramSessionFactory
from neves_be.practice_sessions.services.radicals import RadicalSessionFactory
from neves_be.practice_sessions.types import SessionType
from neves_be.users.models import User
from neves_be.word_lm.models import Word


def make_session_getter(
    user: User,
    session_type: SessionType,
) -> BasePracticeSessionAccessor:
    if session_type == "radicals":
        return RadicalSessionAccessor(user)

    if session_type == "ngrams":
        return NgramSessionAccessor(user)

    assert_never(session_type)


def make_session_serializer(
    session_type: SessionType,
) -> type[serializers.Serializer]:
    if session_type == "radicals":
        return RadicalSessionSerializer

    if session_type == "ngrams":
        return NgramSessionSerializer

    assert_never(session_type)


def make_session_factory(session_type: SessionType, user: User) -> BaseSessionFactory:
    if session_type == "radicals":
        return RadicalSessionFactory(user)

    if session_type == "ngrams":
        return NgramSessionFactory(user)

    assert_never(session_type)


def make_ngrams_stats(request: Request) -> NgramsStatistics:
    session_w_score_within_limits = NgramSession.objects.filter(
        highest_score__gte=70,
    )

    return {
        "isUnlocked": NgramSessionFactory(request.user).get_session_ngrams_qs().count()
        >= NgramSessionFactory.MIN_NGRAMS,
        "progress": Word.objects.filter(
            **{  # noqa: PIE804
                "word_ngrams__ngram__ngram_sessions__session__"
                "in": session_w_score_within_limits,
            },  # type: ignore[misc,unused-ignore]
        ).count()
        / 1000,
    }
