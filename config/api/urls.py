from django.urls import include
from django.urls import path

urlpatterns = [
    path("", include("neves_be.users.api.urls")),
    path("", include("neves_be.radical_sessions.api.urls")),
    path("", include("neves_be.radical_tests.api.urls")),
]
