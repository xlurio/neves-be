from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from neves_be.common.api import error_response
from neves_be.common.api import load_request_data

if TYPE_CHECKING:
    from rest_framework.request import Request


UserModel = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def authenticate_view(request: Request) -> Response:
    data = load_request_data(request)
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
    data = load_request_data(request)
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return error_response(
            "VALIDATION_ERROR",
            "Missing or incorrect data",
            "Username and password are required.",
            http_status=status.HTTP_409_CONFLICT,
        )

    if UserModel.objects.filter(username=username).exists():
        return error_response(
            "USER_EXISTS",
            "Missing or incorrect data",
            "This username is already registered.",
            http_status=status.HTTP_409_CONFLICT,
        )

    user = UserModel.objects.create_user(username=username, password=password)
    return Response(
        {
            "id": str(user.pk),
            "username": user.username,
            "password": password,
        },
        status=status.HTTP_201_CREATED,
    )
