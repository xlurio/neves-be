from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from neves_be.radical_sessions.services import make_radicals_stats
from neves_be.sentence_sessions.services import make_sentences_stats

if TYPE_CHECKING:
    from rest_framework.request import Request


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
