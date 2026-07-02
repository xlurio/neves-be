from typing import assert_never

from rest_framework import serializers
from rest_framework.request import Request

from neves_be.language_model.models import Word
from neves_be.practice_sessions.serializers import RadicalSessionSerializer
from neves_be.practice_sessions.serializers import SentenceSessionSerializer
from neves_be.practice_sessions.services.base import BasePracticeSessionAccessor
from neves_be.practice_sessions.services.base import BaseSessionFactory
from neves_be.practice_sessions.services.base import RadicalSessionAccessor
from neves_be.practice_sessions.services.base import SentenceSessionAccessor
from neves_be.practice_sessions.services.radicals import RadicalSessionFactory
from neves_be.practice_sessions.services.sentences import SentenceSessionFactory
from neves_be.practice_sessions.types import SessionType
from neves_be.sentence_sessions.models import SentenceSession
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
    session_type: SessionType,
) -> type[serializers.Serializer]:
    if session_type == "radicals":
        return RadicalSessionSerializer

    if session_type == "sentences":
        return SentenceSessionSerializer

    assert_never(session_type)


def make_session_factory(session_type: SessionType, user: User) -> BaseSessionFactory:
    if session_type == "radicals":
        return RadicalSessionFactory(user)

    if session_type == "sentences":
        return SentenceSessionFactory(user)

    assert_never(session_type)


def make_sentences_stats(request: Request) -> SentencesStatistics:
    session_w_score_within_limits = SentenceSession.objects.filter(
        highest_score__gte=70,
    )

    return {
        "isUnlocked": SentenceSessionFactory(request.user)
        .get_session_sentences_qs()
        .count()
        >= SentenceSessionFactory.MIN_SENTENCES,
        "progress": Word.objects.filter(
            **{  # noqa: PIE804
                "word_sentences__sentence__sentence_sessions__session__"
                "in": session_w_score_within_limits,
            },  # type: ignore[misc,unused-ignore]
        ).count()
        / 1000,
    }
