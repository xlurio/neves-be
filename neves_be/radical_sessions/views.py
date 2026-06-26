from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical
from neves_be.radical_sessions.serializers import RadicalSessionSerializer
from neves_be.radical_sessions.services import add_radical_to_session
from neves_be.radical_sessions.services import create_radical_session
from neves_be.radical_sessions.services import owned_session_or_404
from neves_be.radicals.models import Radical
from neves_be.radicals.serializers import RadicalSerializer

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import SessionId


class DefaultPagination(PageNumberPagination):
    page_size = 10


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_me_view(request: Request) -> Response:
    radicals_learned = (
        RadicalSessionRadical.objects.filter(
            session__user=request.user,
            session__highest_score__gte=7,
        )
        .values("radical_id")
        .distinct()
        .count()
    )
    progress = round((radicals_learned / 100) * 100, 2)
    return Response(
        {
            "chineseLogographicSystem": {
                "radicalsLearned": radicals_learned,
                "totalRadicals": 100,
                "progress": progress,
            },
        },
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def radical_sessions_view(request: Request) -> Response:
    if request.method == "GET":
        queryset = (
            RadicalSession.objects.filter(user=request.user)
            .annotate(
                num_of_radicals=models.Count("session_radicals"),
            )
            .order_by(
                "-created_at",
            )
        )
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)

        return paginator.get_paginated_response(
            RadicalSessionSerializer(page, many=True).data,
        )

    new_radical_session = create_radical_session(request)
    return Response(RadicalSessionSerializer(new_radical_session).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_session_detail_view(request: Request, session_id: SessionId) -> Response:
    return Response(
        RadicalSessionSerializer(owned_session_or_404(request, session_id)).data,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def radical_session_radicals_view(request: Request, session_id: SessionId) -> Response:
    session = owned_session_or_404(request, session_id)

    if request.method == "GET":
        radicals_qs: QuerySet[Radical] = (
            Radical.objects.filter(
                id__in=session.session_radicals.values("radical_id"),
            )
            .annotate(
                occurrencies=models.Sum("radical_logograms__logogram__occurrences"),
            )
            .order_by("occurrencies")
        )

        paginator = DefaultPagination()
        page = paginator.paginate_queryset(radicals_qs, request)
        serializer = RadicalSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    new_radical = add_radical_to_session(request, session)
    return Response(RadicalSerializer(new_radical).data)
