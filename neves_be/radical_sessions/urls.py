from django.urls import path

from neves_be.radical_sessions.views import radical_session_radicals_view

urlpatterns = [
    path(
        "radicals/sessions/<uuid:session_id>/radicals",
        radical_session_radicals_view,
        name="api-radical-session-radicals",
    ),
]
