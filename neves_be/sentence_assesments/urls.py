from django.urls import path

from neves_be.sentence_assesments.views import sentence_session_assessments_view
from neves_be.sentence_assesments.views import sentence_assessment_answer_view
from neves_be.sentence_assesments.views import sentence_assessment_finish_view
from neves_be.sentence_assesments.views import sentence_assessment_question_view
from neves_be.sentence_assesments.views import sentence_assessment_result_view

urlpatterns = [
    path(
        "sentences/sessions/<uuid:session_id>/tests",
        sentence_session_assessments_view,
        name="api-sentence-session-tests",
    ),
    path(
        "sentences/test/<uuid:assessment_id>/question/<int:question_num>",
        sentence_assessment_question_view,
        name="api-sentence-test-question",
    ),
    path(
        "sentences/test/<uuid:assessment_id>/answer",
        sentence_assessment_answer_view,
        name="api-sentence-test-answer",
    ),
    path(
        "sentences/test/<uuid:assessment_id>/finish",
        sentence_assessment_finish_view,
        name="api-sentence-test-finish",
    ),
    path(
        "sentences/sessions/tests/<uuid:assessment_id>/result",
        sentence_assessment_result_view,
        name="api-sentence-test-result",
    ),
]
