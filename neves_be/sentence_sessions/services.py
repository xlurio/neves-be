from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import functions as dj_funcs
from django.http import Http404

from neves_be.language_model.models import Sentence
from neves_be.language_model.models import SentenceCluster
from neves_be.language_model.models import Word
from neves_be.radical_sessions.exceptions import PracticeSessionCreationError
from neves_be.radical_sessions.models import RadicalSession
from neves_be.sentence_sessions.models import SentenceSession
from neves_be.sentence_sessions.models import SentenceSessionSentence

if TYPE_CHECKING:
    from rest_framework.request import Request

    from neves_be.radical_sessions.types import SentencesStatistics
    from neves_be.radical_sessions.types import SessionId


def get_session_sentences(session: RadicalSession) -> list[Sentence]:
    return [
        session_sentence.sentence
        for session_sentence in SentenceSessionSentence.objects.filter(
            session__user=session.user,
        )
        .select_related(
            "sentence",
        )
        .order_by("position")
    ]


def owned_sentence_session_or_404(
    request: Request,
    session_id: SessionId,
) -> SentenceSession:
    session = (
        SentenceSession.objects.annotate(
            num_of_sentences=models.Count("session_sentences"),
        )
        .filter(id=session_id, user=request.user)
        .first()
    )
    if session is None:
        msg = "Radical session not found."
        raise Http404(msg)
    return session


def annotate_likelihood_to_sentence_qs(
    sentence_qs: models.QuerySet[Sentence],
) -> models.QuerySet[Sentence]:
    total_occurrences = Word.objects.aggregate(
        occurrences_sum=models.Sum("occurrences"),
    )["occurrences_sum"]

    return sentence_qs.annotate(
        likelihood=models.Sum(
            dj_funcs.Ln(
                dj_funcs.Cast(
                    models.F("sentence_words__word__occurrences"),
                    output_field=models.FloatField(),
                )
                / models.Value(
                    float(total_occurrences),
                    output_field=models.FloatField(),
                ),
            ),
        ),
    )


def create_sentence_session(request: Request) -> SentenceSession:
    new_session = SentenceSession.objects.create(user=request.user)

    sentence_session_sentence_sqs = SentenceSessionSentence.objects.filter(
        sentence__cluster_id=models.OuterRef("cluster_id"),
        session__user=request.user,
    ).values("sentence_id")

    maybe_sentence = (
        annotate_likelihood_to_sentence_qs(  # type: ignore[misc]
            Sentence.objects.exclude(
                pk__in=models.Subquery(sentence_session_sentence_sqs),
                cluster__sentencecluster_sessions__session_id__isnull=False,
            ),
        )
        .order_by("-likelihood")
        .first()
    )

    if not maybe_sentence:
        raise PracticeSessionCreationError(
            code="NOT_ENOUGH_RADICALS",
            title="Not enough radicals",
            details="Learn more radicals before continuing to practice sentences.",
        )

    cluster = maybe_sentence.cluster

    assert cluster

    most_likely_sequences_in_cluster_qs = annotate_likelihood_to_sentence_qs(
        cluster.sentences.get_queryset(),
    ).order_by("-likelihood")[:3]  # type: ignore[misc]

    session_sentences_to_create = []

    for sentence_idx, sentence in enumerate(most_likely_sequences_in_cluster_qs):
        session_sentences_to_create.append(
            SentenceSessionSentence(
                session=new_session,
                sentence=sentence,
                sentence_cluster=cluster,
                position=sentence_idx,
            ),
        )

    SentenceSessionSentence.objects.bulk_create(session_sentences_to_create)

    return new_session


def make_sentences_stats(request: Request) -> SentencesStatistics:
    return {
        "is_unlocked": RadicalSession.objects.filter(
            user=request.user,
            highest_score__gte=70,
        ).exists(),
        "progress": SentenceCluster.objects.filter(
            sentencecluster_sessions__session__highest_score__gte=70,  # type: ignore[misc,unused-ignore]
        ).count()
        / SentenceCluster.objects.all().count(),
    }
