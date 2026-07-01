from django.urls import path

from neves_be.practice_assessments.views import practice_assessment_finish_view
from neves_be.practice_assessments.views import practice_assessment_result_view
from neves_be.practice_assessments.views import practice_session_assessments_view

urlpatterns = [
    path(
        "<slug:session_type>/sessions/<uuid:session_id>/assessments",
        practice_session_assessments_view,
        name="api-practice-session-assessments",
    ),
    path(
        "<slug:session_type>/assessment/<uuid:assessment_id>/finish",
        practice_assessment_finish_view,
        name="api-practice-assessment-finish",
    ),
    path(
        "<slug:session_type>/sessions/assessments/<uuid:assessment_id>/result",
        practice_assessment_result_view,
        name="api-practice-assessment-result",
    ),
]
