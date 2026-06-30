from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.http import Http404

from neves_be.language_model.models import LogogramWordMap
from neves_be.language_model.models import Radical
from neves_be.language_model.models import RadicalLogogramMap
from neves_be.language_model.models import Word
from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import RadicalSessionId
    from neves_be.radical_sessions.types import RadicalsStatistics


def owned_radical_session_or_404(
    request: Request,
    session_id: RadicalSessionId,
) -> RadicalSession:
    session = (
        RadicalSession.objects.annotate(
            num_of_radicals=models.Count("session_radicals"),
        )
        .filter(id=session_id, user=request.user)
        .first()
    )
    if session is None:
        msg = "Radical session not found."
        raise Http404(msg)
    return session


def create_radical_session(request: Request) -> RadicalSession:
    return RadicalSession.objects.create(user=request.user)


def add_radical_to_session(request: Request, session: RadicalSession) -> Radical:
    new_radical = (
        Radical.objects.exclude(radical_sessions__session__user=request.user)
        .annotate(
            occurrencies=models.Sum("radical_logograms__logogram__occurrences"),
        )
        .order_by("-occurrencies")
        .first()
    )

    assert new_radical

    position = RadicalSessionRadical.objects.filter(session=session).count()
    RadicalSessionRadical.objects.create(
        session=session,
        radical=new_radical,
        position=position,
    )

    return new_radical


def make_radicals_stats(request: Request) -> RadicalsStatistics:
    most_common_words = Word.objects.order_by("-occurrences")[:1000].values_list("pk")
    most_common_logograms = LogogramWordMap.objects.filter(
        word_id__in=most_common_words,
    ).values_list("logogram_id")
    most_common_radicals = RadicalLogogramMap.objects.filter(
        logogram_id__in=most_common_logograms,
    ).values_list("radical_id")
    radicals_learned = (
        RadicalSessionRadical.objects.filter(
            session__user=request.user,
            session__highest_score__gte=70,
            radical_id__in=most_common_radicals,
        )
        .values("radical_id")
        .distinct()
        .count()
    )
    radicals_progress = round((radicals_learned / 100) * 100, 2)

    return {
        "progress": radicals_progress,
    }
