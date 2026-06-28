from __future__ import annotations

from rest_framework import serializers

from neves_be.practice_sessions.serializers import PracticeSessionSerializer


class RadicalSessionSerializer(PracticeSessionSerializer):
    num_of_radicals = serializers.IntegerField(read_only=True)

    camel_case_aliases = {
        "created_at": "createdAt",
        "num_of_radicals": "numOfRadicals",
        "highest_score": "highestScore",
    }
