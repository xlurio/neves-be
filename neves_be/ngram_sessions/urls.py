from django.urls import path

from neves_be.ngram_sessions.views import ngram_session_ngram_words_view
from neves_be.ngram_sessions.views import ngram_session_ngrams_view
from neves_be.ngram_sessions.views import ngram_session_word_logogram_view

urlpatterns = [
    path(
        "ngrams/sessions/<uuid:session_id>/ngrams/<int:ngram_num>",
        ngram_session_ngrams_view,
        name="api-ngram-session-ngrams",
    ),
    path(
        "ngrams/sessions/<uuid:session_id>/ngrams/<int:ngram_num>/words/<int:word_num>",
        ngram_session_ngram_words_view,
        name="api-ngram-session-ngram-word",
    ),
    path(
        "ngrams/sessions/<uuid:session_id>/ngrams/<int:ngram_num>/words/"
        "<int:word_num>/logograms/<int:logogram_num>",
        ngram_session_word_logogram_view,
        name="api-ngram-session-word-logogram",
    ),
]
