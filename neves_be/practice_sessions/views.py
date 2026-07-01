from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.practice_sessions.services.utils import make_sentences_stats
from neves_be.practice_sessions.services.utils import make_session_factory
from neves_be.practice_sessions.services.utils import make_session_getter
from neves_be.practice_sessions.services.utils import make_session_serializer
from neves_be.radical_sessions.services import make_radicals_stats

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.practice_sessions.types import ConcretePracticeSessionId
    from neves_be.practice_sessions.types import SessionType


class DefaultPagination(PageNumberPagination):
    page_size = 10


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_me_view(request: Request) -> Response:
    return Response(
        {
            "radicals": make_radicals_stats(request),
            "sentences": make_sentences_stats(request),
        },
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def practice_sessions_view(request: Request, session_type: SessionType) -> Response:
    serializer_cls = make_session_serializer(session_type)

    if request.method == "GET":
        getter = make_session_getter(request.user, session_type)
        queryset = getter.get_sessions()
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)

        return paginator.get_paginated_response(
            serializer_cls(page, many=True).data,
        )

    factory = make_session_factory(session_type, request.user)
    new_practice_session = factory.make_assessment()

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
