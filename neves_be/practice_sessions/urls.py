from django.urls import path

from neves_be.practice_sessions.views import stats_me_view

urlpatterns = [
    path("stats/me", stats_me_view, name="api-stats-me"),
]
