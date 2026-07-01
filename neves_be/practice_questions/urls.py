from django.urls import path

from neves_be.practice_questions.views import practice_assessment_answer_view
from neves_be.practice_questions.views import practice_assessment_question_view

urlpatterns = [
    path(
        "<slug:session_type>/assessment/<uuid:assessment_id>/question/<int:question_num>",
        practice_assessment_question_view,
        name="api-practice-assessment-question",
    ),
    path(
        "<slug:session_type>/assessment/<uuid:assessment_id>/answer",
        practice_assessment_answer_view,
        name="api-practice-assessment-answer",
    ),
]
