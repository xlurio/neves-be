from django.urls import path

from neves_be.practice_assessments.views import practice_assessment_finish_view
from neves_be.practice_assessments.views import practice_assessment_result_view
from neves_be.practice_assessments.views import practice_session_assessments_view

urlpatterns = [
    path(
        "<slug:session_type>/sessions/<uuid:session_id>/tests",
        practice_session_assessments_view,
        name="api-practice-session-tests",
    ),
    path(
        "<slug:session_type>/test/<uuid:assessment_id>/finish",
        practice_assessment_finish_view,
        name="api-practice-test-finish",
    ),
    path(
        "<slug:session_type>/sessions/tests/<uuid:assessment_id>/result",
        practice_assessment_result_view,
        name="api-practice-test-result",
    ),
]
