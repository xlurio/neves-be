from django.urls import path

from neves_be.sentence_sessions.views import sentence_session_detail_view
from neves_be.sentence_sessions.views import sentence_sessions_view

urlpatterns = [
    path("sentences/sessions", sentence_sessions_view, name="api-sentence-sessions"),
    path(
        "sentences/sessions/<uuid:session_id>",
        sentence_session_detail_view,
        name="api-sentence-session-detail",
    ),
]
