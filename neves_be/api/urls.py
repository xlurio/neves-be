from django.urls import path

from neves_be.api import views

urlpatterns = [
    path("authenticate", views.authenticate_view, name="api-authenticate"),
    path("users", views.user_create_view, name="api-users-create"),
    path("stats/me", views.stats_me_view, name="api-stats-me"),
    path("radicals/sessions", views.radical_sessions_view, name="api-radical-sessions"),
    path("radicals/sessions/<uuid:session_id>", views.radical_session_detail_view, name="api-radical-session-detail"),
    path("radicals/sessions/<uuid:session_id>/radicals", views.radical_session_radicals_view, name="api-radical-session-radicals"),
    path("radicals/sessions/<uuid:session_id>/tests", views.radical_session_tests_view, name="api-radical-session-tests"),
    path("radicals/test/<uuid:test_id>/question/<int:question_num>", views.radical_test_question_view, name="api-radical-test-question"),
    path("radicals/test/<uuid:test_id>/answer", views.radical_test_answer_view, name="api-radical-test-answer"),
    path("radicals/test/<uuid:test_id>/finish", views.radical_test_finish_view, name="api-radical-test-finish"),
    path("radicals/sessions/tests/<uuid:test_id>/result", views.radical_test_result_view, name="api-radical-test-result"),
]
