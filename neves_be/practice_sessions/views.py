from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from django.db import models
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.ngram_sessions.models import NgramSession
from neves_be.ngram_sessions.models import NgramSessionRequest
from neves_be.practice_sessions.services.utils import make_ngrams_stats
from neves_be.practice_sessions.services.utils import make_session_factory
from neves_be.practice_sessions.services.utils import make_session_getter
from neves_be.practice_sessions.services.utils import make_session_serializer
from neves_be.radical_sessions.services import make_radicals_stats

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_sessions.types import ConcretePracticeSessionId
    from neves_be.practice_sessions.types import SessionType
    from neves_be.users.models import User


class DefaultPagination(PageNumberPagination):
    page_size = 10


def _make_pending_ngram_entries(user: User) -> list[dict[str, Any]]:
    pending_requests = NgramSessionRequest.objects.filter(
        user=user,
        finished_at__isnull=True,
        request_session__isnull=True,
    ).values("id", "started_at")

    return [
        {
            "id": request["id"],
            "created_at": request["started_at"],
            "highest_score": 0,
            "num_of_ngrams": 0,
            "is_ready": False,
        }
        for request in pending_requests
    ]


def _make_ngram_list_payload(user: User) -> list[dict[str, Any]]:
    ready_sessions = list(
        NgramSession.objects.filter(user=user)
        .annotate(
            num_of_ngrams=models.Count("session_ngrams"),
            is_ready=models.Value(
                value=True,
                output_field=models.BooleanField(),
            ),
        )
        .values(
            "id",
            "created_at",
            "highest_score",
            "num_of_ngrams",
            "is_ready",
        ),
    )
    merged_payload = [*ready_sessions, *_make_pending_ngram_entries(user)]

    return sorted(
        merged_payload,
        key=lambda item: item["created_at"],
        reverse=True,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_me_view(request: Request) -> Response:
    return Response(
        {
            "username": cast("User", request.user).username,
            "radicals": make_radicals_stats(request),
            "ngrams": make_ngrams_stats(request),
        },
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def practice_sessions_view(request: Request, session_type: SessionType) -> Response:
    serializer_cls = make_session_serializer(session_type)

    if request.method == "GET":
        paginator = DefaultPagination()

        if session_type == "ngrams":
            queryset = _make_ngram_list_payload(cast("User", request.user))
        else:
            getter = make_session_getter(request.user, session_type)
            queryset = getter.get_sessions()

        page = paginator.paginate_queryset(queryset, request)

        return paginator.get_paginated_response(
            serializer_cls(page, many=True).data,
        )

    factory = make_session_factory(session_type, request.user)
    new_practice_session = factory.make_session()

    return Response(serializer_cls(new_practice_session).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def practice_session_detail_view(
    request: Request,
    session_type: SessionType,
    session_id: ConcretePracticeSessionId,
) -> Response:
    serializer_cls = make_session_serializer(session_type)
    getter = make_session_getter(request.user, session_type)

    return Response(
        serializer_cls(
            getter.get_session(session_id),
        ).data,
    )
