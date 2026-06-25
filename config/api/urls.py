from django.urls import include
from django.urls import path

from neves_be.users.urls import api_urlpatterns as users_api_urlpatterns

urlpatterns = [
    path("", include(users_api_urlpatterns)),
    path("", include("neves_be.radical_sessions.urls")),
    path("", include("neves_be.radical_tests.urls")),
]
