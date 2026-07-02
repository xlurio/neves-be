from collections.abc import MutableMapping
from typing import Any

from rest_framework import serializers
from rest_framework.fields import Field

from neves_be.char_lm.models import Logogram
from neves_be.char_lm.models import Radical
from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.lang_model.serializers import PronounceOrGenerateMixin


class RadicalSerializer(
    CamelCaseAliasSerializerMixin,
    PronounceOrGenerateMixin,
    serializers.ModelSerializer,
):
    pronounce = serializers.SerializerMethodField()

    class Meta:
        model = Radical
        fields = [
            "id",
            "pinyin",
            "meaning",
            "pronounce",
        ]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


class LogogramSerializer(
    CamelCaseAliasSerializerMixin,
    PronounceOrGenerateMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = Logogram
        fields = ["id", "pinyin", "meaning", "pronounce"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()

        return self._rename_camel_case_fields(fields)

    def get_radicals(self, instance: Logogram) -> list[dict[str, Any]]:
        radical_ids = instance.logogram_radicals.values_list("logogram_id", flat=True)
        radical_qs = Radical.objects.filter(pk__in=radical_ids)

        return RadicalSerializer(radical_qs, many=True)
