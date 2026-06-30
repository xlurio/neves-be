from django.urls import path

from neves_be.practice_sessions.views import practice_session_detail_view
from neves_be.practice_sessions.views import practice_sessions_view
from neves_be.practice_sessions.views import stats_me_view

urlpatterns = [
    path("stats/me", stats_me_view, name="api-stats-me"),
    path(
        "<slug:session_type>/sessions",
        practice_sessions_view,
        name="api-practice-sessions",
    ),
    path(
        "<slug:session_type>/sessions/<uuid:session_id>",
        practice_session_detail_view,
        name="api-practice-session-detail",
    ),
]
