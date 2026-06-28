from __future__ import annotations

from rest_framework import serializers

from neves_be.practice_sessions.serializers import PracticeSessionSerializer


class SentenceSessionSerializer(PracticeSessionSerializer):
    num_of_sentences = serializers.IntegerField(read_only=True)

    camel_case_aliases = {
        "created_at": "createdAt",
        "num_of_sentences": "numOfSentences",
        "highest_score": "highestScore",
    }
