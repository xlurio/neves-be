from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.http import Http404

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical
from neves_be.radicals.models import Radical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import SessionId


def get_session_radicals(session: RadicalSession) -> list[Radical]:
    return [
        session_radical.radical
        for session_radical in session.session_radicals.select_related(
            "radical",
        ).order_by("position")
    ]


def owned_session_or_404(request: Request, session_id: SessionId) -> RadicalSession:
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
        .order_by("occurrencies")
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
