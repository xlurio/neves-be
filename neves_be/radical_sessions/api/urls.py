from django.urls import path

from neves_be.radical_sessions.views import radical_session_detail_view
from neves_be.radical_sessions.views import radical_session_radicals_view
from neves_be.radical_sessions.views import radical_sessions_view
from neves_be.radical_sessions.views import stats_me_view

urlpatterns = [
    path("stats/me", stats_me_view, name="api-stats-me"),
    path("radicals/sessions", radical_sessions_view, name="api-radical-sessions"),
    path(
        "radicals/sessions/<uuid:session_id>",
        radical_session_detail_view,
        name="api-radical-session-detail",
    ),
    path(
        "radicals/sessions/<uuid:session_id>/radicals",
        radical_session_radicals_view,
        name="api-radical-session-radicals",
    ),
]
