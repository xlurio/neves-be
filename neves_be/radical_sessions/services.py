from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction
from django.http import Http404

from neves_be.radical_sessions.models import RadicalSession
from neves_be.radical_sessions.models import RadicalSessionRadical
from neves_be.radicals.models import Radical

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import SessionId
    from neves_be.users.models import User

DEFAULT_SESSION_RADICAL_LIMIT = 20


def get_session_radicals(session: RadicalSession) -> list[Radical]:
    linked_radicals = [
        session_radical.radical
        for session_radical in session.session_radicals.select_related(
            "radical",
        ).order_by("position")
    ]
    if linked_radicals:
        return linked_radicals
    return list(Radical.objects.order_by("id")[:DEFAULT_SESSION_RADICAL_LIMIT])


def owned_session_or_404(request: Request, session_id: SessionId) -> RadicalSession:
    session = RadicalSession.objects.filter(id=session_id, user=request.user).first()
    if session is None:
        msg = "Radical session not found."
        raise Http404(msg)
    return session


def ensure_user_default_session(user: User) -> None:
    if RadicalSession.objects.filter(user=user).exists():
        return

    radicals = list(Radical.objects.order_by("id")[:DEFAULT_SESSION_RADICAL_LIMIT])
    if not radicals:
        return

    with transaction.atomic():
        session = RadicalSession.objects.create(
            user=user,
            num_of_radicals=len(radicals),
        )
        RadicalSessionRadical.objects.bulk_create(
            [
                RadicalSessionRadical(
                    session=session,
                    radical=radical,
                    position=position,
                )
                for position, radical in enumerate(radicals, start=1)
            ],
        )
