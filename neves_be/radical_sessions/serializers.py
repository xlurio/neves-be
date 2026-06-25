from __future__ import annotations

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.radical_sessions.models import RadicalSession


class RadicalSessionSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "created_at": "createdAt",
        "num_of_radicals": "numOfRadicals",
        "highest_score": "highestScore",
    }

    class Meta:
        model = RadicalSession
        fields = ["id", "created_at", "num_of_radicals", "highest_score"]

    def get_fields(self):
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)
