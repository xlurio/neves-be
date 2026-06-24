from __future__ import annotations

import random
from json import JSONDecodeError

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.db import models
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from neves_be.api.serializers import RadicalSerializer
from neves_be.api.serializers import RadicalSessionSerializer
from neves_be.api.serializers import RadicalSessionTestSerializer
from radicals.models import Radical
from radicals.models import RadicalSession
from radicals.models import RadicalSessionRadical
from radicals.models import RadicalSessionTest
from radicals.models import RadicalSessionTestQuestion

User = get_user_model()
ANSWER_CHOICES = ["a", "b", "c", "d", "e"]
QUESTION_TYPES = [
    RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING,
    RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN,
    RadicalSessionTestQuestion.Type.MEANING_TO_LOGOGRAM,
    RadicalSessionTestQuestion.Type.PINYIN_TO_LOGOGRAM,
]


class DefaultPagination(PageNumberPagination):
    page_size = 10


def error_response(code: str, title: str, details: str, *, http_status: int, payload: dict | None = None) -> Response:
    response_payload: dict[str, object] = {
        "code": code,
        "title": title,
        "details": details,
    }
    if payload is not None:
        response_payload["payload"] = payload
    return Response(response_payload, status=http_status)


def _safe_pronounce_url(request: Request, pronounce: str) -> str:
    if not pronounce:
        return ""
    if pronounce.startswith("http://") or pronounce.startswith("https://"):
        return pronounce
    if pronounce.startswith("/"):
        return request.build_absolute_uri(pronounce)
    return pronounce


def _load_request_data(request: Request) -> dict:
    if isinstance(request.data, dict):
        return request.data
    try:
        return dict(request.data)
    except (TypeError, ValueError, JSONDecodeError):
        return {}


def _pick_option_radicals(correct: Radical, pool: list[Radical], rng: random.Random) -> list[Radical]:
    distractors = [radical for radical in pool if radical.id != correct.id]
    selected = rng.sample(distractors, k=4)
    options = [*selected, correct]
    rng.shuffle(options)
    return options


def _question_text(radical: Radical, question_type: str) -> str:
    if question_type == RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM:
        return "What logogram corresponds to the following audio?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO:
        return f"What pronounce corresponds the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING:
        return f"What meaning corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN:
        return f"What pinyin corresponds to the logogram {radical.id}?"
    if question_type == RadicalSessionTestQuestion.Type.MEANING_TO_LOGOGRAM:
        return f'What logogram corresponds to the meaning "{radical.meaning}"?'
    return f'What logogram corresponds to the pinyin "{radical.pinyin}"?'


def _build_alternatives(request: Request, question_type: str, options: list[Radical]) -> list[dict[str, str]]:
    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_AUDIO:
        return [
            {
                "type": "AUDIO",
                "payload": _safe_pronounce_url(request, option.pronounce),
            }
            for option in options
        ]

    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_MEANING:
        return [{"type": "TEXT", "payload": option.meaning} for option in options]

    if question_type == RadicalSessionTestQuestion.Type.LOGOGRAM_TO_PINYIN:
        return [{"type": "TEXT", "payload": option.pinyin} for option in options]

    return [{"type": "TEXT", "payload": option.id} for option in options]


def _get_session_radicals(session: RadicalSession) -> list[Radical]:
    linked_radicals = [
        session_radical.radical
        for session_radical in session.session_radicals.select_related("radical").order_by("position")
    ]
    if linked_radicals:
        return linked_radicals
    return list(Radical.objects.order_by("id")[:20])


def _serialize_question_payload(question: RadicalSessionTestQuestion, request: Request) -> dict:
    payload: dict[str, object] = {
        "type": question.type,
        "question": question.question,
        "alternatives": question.alternatives,
        "currAnswer": question.curr_answer,
    }
    if question.audio:
        payload["audio"] = _safe_pronounce_url(request, question.audio)
    return payload


def _owned_session_or_404(request: Request, session_id) -> RadicalSession:  # noqa: ANN001
    return get_object_or_404(RadicalSession, id=session_id, user=request.user)


def _owned_test_or_404(request: Request, test_id) -> RadicalSessionTest:  # noqa: ANN001
    return get_object_or_404(RadicalSessionTest.objects.select_related("session"), id=test_id, session__user=request.user)


def _ensure_user_default_session(user) -> None:  # noqa: ANN001
    if RadicalSession.objects.filter(user=user).exists():
        return

    radicals = list(Radical.objects.order_by("id")[:20])
    if not radicals:
        return

    with transaction.atomic():
        session = RadicalSession.objects.create(user=user, num_of_radicals=len(radicals))
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


@api_view(["POST"])
@permission_classes([AllowAny])
def authenticate_view(request: Request) -> Response:
    data = _load_request_data(request)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return error_response(
            "INVALID_CREDENTIALS",
            "Failed to authenticate",
            "Username and password are required.",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return error_response(
            "INVALID_CREDENTIALS",
            "Failed to authenticate",
            "Invalid username or password.",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    login(request, user)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def user_create_view(request: Request) -> Response:
    data = _load_request_data(request)
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return error_response(
            "VALIDATION_ERROR",
            "Missing or incorrect data",
            "Username and password are required.",
            http_status=status.HTTP_409_CONFLICT,
        )

    if User.objects.filter(username=username).exists():
        return error_response(
            "USER_EXISTS",
            "Missing or incorrect data",
            "This username is already registered.",
            http_status=status.HTTP_409_CONFLICT,
        )

    user = User.objects.create_user(username=username, password=password)
    return Response(
        {
            "id": str(user.pk),
            "username": user.username,
            "password": password,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_me_view(request: Request) -> Response:
    total_radicals = Radical.objects.count()
    radicals_learned = RadicalSessionRadical.objects.filter(session__user=request.user).values("radical_id").distinct().count()
    progress = round((radicals_learned / total_radicals) * 100, 2) if total_radicals else 0.0

    return Response(
        {
            "chineseLogographicSystem": {
                "radicalsLearned": radicals_learned,
                "totalRadicals": total_radicals,
                "progress": progress,
            },
        },
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_sessions_view(request: Request) -> Response:
    _ensure_user_default_session(request.user)
    queryset = RadicalSession.objects.filter(user=request.user).order_by("-created_at")
    paginator = DefaultPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = RadicalSessionSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_session_detail_view(request: Request, session_id) -> Response:  # noqa: ANN001
    session = _owned_session_or_404(request, session_id)
    serializer = RadicalSessionSerializer(session)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_session_radicals_view(request: Request, session_id) -> Response:  # noqa: ANN001
    session = _owned_session_or_404(request, session_id)

    radicals_qs: QuerySet[Radical] = Radical.objects.filter(
        id__in=session.session_radicals.values("radical_id"),
    ).order_by("id")

    if not radicals_qs.exists():
        radicals_qs = Radical.objects.order_by("id")[: session.num_of_radicals or 20]

    paginator = DefaultPagination()
    page = paginator.paginate_queryset(radicals_qs, request)
    serializer = RadicalSerializer(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def radical_session_tests_view(request: Request, session_id) -> Response:  # noqa: ANN001
    session = _owned_session_or_404(request, session_id)

    if request.method == "GET":
        queryset = session.tests.order_by("-finished_at", "id")
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RadicalSessionTestSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    session_radicals = _get_session_radicals(session)
    pool = list(Radical.objects.order_by("id"))
    if len(pool) < 5 or not session_radicals:
        return error_response(
            "NOT_ENOUGH_RADICALS",
            "Could not create test",
            "At least five radicals are required to generate a test.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        test = RadicalSessionTest.objects.create(session=session)
        rng = random.Random(test.id.int)
        questions: list[RadicalSessionTestQuestion] = []

        for number, radical in enumerate(session_radicals, start=1):
            question_type = QUESTION_TYPES[(number - 1) % len(QUESTION_TYPES)]
            options = _pick_option_radicals(radical, pool, rng)
            alternatives = _build_alternatives(request, question_type, options)
            expected_answer = ANSWER_CHOICES[options.index(radical)]

            questions.append(
                RadicalSessionTestQuestion(
                    test=test,
                    number=number,
                    type=question_type,
                    question=_question_text(radical, question_type),
                    alternatives=alternatives,
                    audio=radical.pronounce if question_type == RadicalSessionTestQuestion.Type.AUDIO_TO_LOGOGRAM else "",
                    expected_answer=expected_answer,
                ),
            )

        RadicalSessionTestQuestion.objects.bulk_create(questions)

    serializer = RadicalSessionTestSerializer(test)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_test_question_view(request: Request, test_id, question_num: int) -> Response:  # noqa: ANN001
    test = _owned_test_or_404(request, test_id)
    total_questions = test.questions.count()

    question = get_object_or_404(test.questions, number=question_num)

    next_url = None
    previous_url = None
    if question_num < total_questions:
        next_url = request.build_absolute_uri(
            reverse("api-radical-test-question", kwargs={"test_id": str(test.id), "question_num": question_num + 1}),
        )
    if question_num > 1:
        previous_url = request.build_absolute_uri(
            reverse("api-radical-test-question", kwargs={"test_id": str(test.id), "question_num": question_num - 1}),
        )

    return Response(
        {
            "count": total_questions,
            "next": next_url,
            "previous": previous_url,
            "id": str(test.id),
            "payload": _serialize_question_payload(question, request),
        },
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def radical_test_answer_view(request: Request, test_id) -> Response:  # noqa: ANN001
    test = _owned_test_or_404(request, test_id)
    data = _load_request_data(request)

    try:
        question_num = int(data.get("questionNum"))
    except (TypeError, ValueError):
        return error_response(
            "INVALID_QUESTION",
            "Invalid question",
            "A valid question number is required.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    answer = str(data.get("answer", "")).lower()
    if answer not in ANSWER_CHOICES:
        return error_response(
            "INVALID_ANSWER",
            "Invalid answer",
            "Answer must be one of: a, b, c, d, e.",
            http_status=status.HTTP_400_BAD_REQUEST,
        )

    question = test.questions.filter(number=question_num).first()
    if question is None:
        return error_response(
            "QUESTION_MISSED",
            "Question not found",
            "The requested question does not exist for this test.",
            http_status=status.HTTP_409_CONFLICT,
            payload={"questionMissed": question_num},
        )

    question.curr_answer = answer
    question.save(update_fields=["curr_answer"])
    return Response({"status": "ok"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def radical_test_finish_view(request: Request, test_id) -> Response:  # noqa: ANN001
    test = _owned_test_or_404(request, test_id)

    unanswered_question = test.questions.filter(curr_answer__isnull=True).order_by("number").first()
    if unanswered_question is not None:
        return error_response(
            "QUESTION_MISSED",
            "Question was missed",
            "At least one question has not been answered.",
            http_status=status.HTTP_409_CONFLICT,
            payload={"questionMissed": unanswered_question.number},
        )

    total_questions = test.questions.count()
    correct_answers = test.questions.filter(curr_answer=models.F("expected_answer")).count()
    score = int(round((correct_answers / total_questions) * 100)) if total_questions else 0

    test.score = score
    test.finished_at = timezone.now()
    test.save(update_fields=["score", "finished_at"])

    session = test.session
    if score > session.highest_score:
        session.highest_score = score
        session.save(update_fields=["highest_score"])

    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def radical_test_result_view(request: Request, test_id) -> Response:  # noqa: ANN001
    test = _owned_test_or_404(request, test_id)

    questions_payload: list[dict[str, object]] = []
    for question in test.questions.order_by("number"):
        question_payload: dict[str, object] = {
            "type": question.type,
            "question": question.question,
            "alternatives": question.alternatives,
            "currAnswer": question.curr_answer or "a",
            "expectedAnswer": question.expected_answer,
        }
        if question.audio:
            question_payload["audio"] = _safe_pronounce_url(request, question.audio)
        questions_payload.append(question_payload)

    return Response(
        {
            "id": str(test.id),
            "score": test.score,
            "questions": questions_payload,
        },
    )
