from django.urls import path

from neves_be.sentence_sessions.views import sentence_session_sentence_words_view
from neves_be.sentence_sessions.views import sentence_session_sentences_view
from neves_be.sentence_sessions.views import sentence_session_word_logogram_view

urlpatterns = [
    path(
        "sentences/sessions/<uuid:session_id>/sentences/<int:sentence_num>",
        sentence_session_sentences_view,
        name="api-sentence-session-sentences",
    ),
    path(
        "sentences/sessions/<uuid:session_id>/sentences/<int:sentence_num>/words/"
        "<int:word_num>",
        sentence_session_sentence_words_view,
        name="api-sentence-session-sentence-word",
    ),
    path(
        "sentences/sessions/<uuid:session_id>/sentences/<int:sentence_num>/words/"
        "<int:word_num>/logograms/<int:logogram_num>",
        sentence_session_word_logogram_view,
        name="api-sentence-session-word-logogram",
    ),
]
