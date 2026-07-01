from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from rest_framework.fields import Field


class PracticeSessionSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.Serializer,
):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    highest_score = serializers.IntegerField()

    camel_case_aliases = {
        "created_at": "createdAt",
        "highest_score": "highestScore",
    }

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()

        return self._rename_camel_case_fields(fields)


class RadicalSessionSerializer(PracticeSessionSerializer):
    num_of_radicals = serializers.IntegerField(read_only=True)

    camel_case_aliases = {
        "created_at": "createdAt",
        "num_of_radicals": "numOfRadicals",
        "highest_score": "highestScore",
    }


class SentenceSessionSerializer(PracticeSessionSerializer):
    num_of_sentences = serializers.IntegerField(read_only=True)

    camel_case_aliases = {
        "created_at": "createdAt",
        "num_of_sentences": "numOfSentences",
        "highest_score": "highestScore",
    }
