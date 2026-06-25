from django.urls import path

from neves_be.radical_tests.views import radical_session_tests_view
from neves_be.radical_tests.views import radical_test_answer_view
from neves_be.radical_tests.views import radical_test_finish_view
from neves_be.radical_tests.views import radical_test_question_view
from neves_be.radical_tests.views import radical_test_result_view

urlpatterns = [
    path(
        "radicals/sessions/<uuid:session_id>/tests",
        radical_session_tests_view,
        name="api-radical-session-tests",
    ),
    path(
        "radicals/test/<uuid:test_id>/question/<int:question_num>",
        radical_test_question_view,
        name="api-radical-test-question",
    ),
    path(
        "radicals/test/<uuid:test_id>/answer",
        radical_test_answer_view,
        name="api-radical-test-answer",
    ),
    path(
        "radicals/test/<uuid:test_id>/finish",
        radical_test_finish_view,
        name="api-radical-test-finish",
    ),
    path(
        "radicals/sessions/tests/<uuid:test_id>/result",
        radical_test_result_view,
        name="api-radical-test-result",
    ),
]
