from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

import celery
from django.db import transaction
from django.utils import timezone

from neves_be.ngram_sessions.models import NgramSessionRequest
from neves_be.users.models import User

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.common.types import CeleryTaskOutputSchema
    from neves_be.users.types import UserId


@celery.shared_task
@transaction.atomic
def async_create_ngram_session(user_id: UserId) -> CeleryTaskOutputSchema:
    from neves_be.practice_sessions.services.ngrams import NgramSessionFactory  # noqa: I001, PLC0415
    from neves_be.practice_assessments.services.factories.ngrams import (  # noqa: PLC0415
        NgramAssessmentFactory,
    )

    user = User.objects.get(pk=user_id)

    request = NgramSessionRequest.objects.create(user=user)

    session = NgramSessionFactory(user).make_session_async(request)
    NgramAssessmentFactory(cast("Request", None)).make_assessment(session)

    request.finished_at = timezone.now()
    request.save(update_fields=["finished_at"])

    return {
        "did_succeed": True,
        "payload": {"user": {"id": user.pk, "username": user.username}},
    }
