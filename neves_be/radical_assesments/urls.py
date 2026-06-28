from django.urls import path

from neves_be.radical_assesments.views import radical_session_assessments_view
from neves_be.radical_assesments.views import radical_assessment_answer_view
from neves_be.radical_assesments.views import radical_assessment_finish_view
from neves_be.radical_assesments.views import radical_assessment_question_view
from neves_be.radical_assesments.views import radical_assessment_result_view

urlpatterns = [
    path(
        "radicals/sessions/<uuid:session_id>/tests",
        radical_session_assessments_view,
        name="api-radical-session-tests",
    ),
    path(
        "radicals/test/<uuid:assessment_id>/question/<int:question_num>",
        radical_assessment_question_view,
        name="api-radical-test-question",
    ),
    path(
        "radicals/test/<uuid:assessment_id>/answer",
        radical_assessment_answer_view,
        name="api-radical-test-answer",
    ),
    path(
        "radicals/test/<uuid:assessment_id>/finish",
        radical_assessment_finish_view,
        name="api-radical-test-finish",
    ),
    path(
        "radicals/sessions/tests/<uuid:assessment_id>/result",
        radical_assessment_result_view,
        name="api-radical-test-result",
    ),
]
