from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.language_model.models import Radical
from neves_be.language_model.serializers import RadicalSerializer
from neves_be.practice_sessions.services.utils import make_session_getter
from neves_be.practice_sessions.views import DefaultPagination
from neves_be.radical_sessions.services import add_radical_to_session

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import RadicalSessionId


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def radical_session_radicals_view(
    request: Request,
    session_id: RadicalSessionId,
) -> Response:
    getter = make_session_getter(request.user, "radicals")
    session = getter.get_session(session_id)

    if request.method == "GET":
        radicals_qs: QuerySet[Radical] = (
            Radical.objects.filter(
                id__in=session.session_radicals.values("radical_id"),
            )
            .annotate(
                occurrencies=models.Sum("radical_logograms__logogram__occurrences"),
            )
            .order_by("-occurrencies")
        )

        paginator = DefaultPagination()
        page = paginator.paginate_queryset(radicals_qs, request)
        serializer = RadicalSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    new_radical = add_radical_to_session(request, session)
    return Response(RadicalSerializer(new_radical).data)
