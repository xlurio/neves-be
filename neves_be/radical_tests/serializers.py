from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.radical_tests.models import RadicalSessionTest

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from rest_framework.fields import Field


class RadicalSessionTestSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "finished_at": "finishedAt",
    }

    class Meta:
        model = RadicalSessionTest
        fields = ["id", "finished_at", "score"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)
