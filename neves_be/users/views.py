from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from neves_be.common.api import error_response
from neves_be.common.api import load_request_data
from neves_be.users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from rest_framework.request import Request


UserModel = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


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
