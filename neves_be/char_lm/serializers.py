from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from rest_framework import serializers

from neves_be.char_lm.models import Logogram
from neves_be.char_lm.models import Radical
from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.lang_model.serializers import PronounceOrGenerateMixin

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from rest_framework.fields import Field


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

    def _get_input_text(self, instance):
        assert isinstance(instance, Radical)

        return instance.id


class LogogramSerializer(
    CamelCaseAliasSerializerMixin,
    PronounceOrGenerateMixin,
    serializers.ModelSerializer,
):
    pronounce = serializers.SerializerMethodField()
    radicals = serializers.SerializerMethodField()

    class Meta:
        model = Logogram
        fields = ["id", "pinyin", "meaning", "pronounce", "radicals"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()

        return self._rename_camel_case_fields(fields)

    def get_radicals(self, instance: Logogram) -> list[dict[str, Any]]:
        radical_ids = instance.logogram_radicals.values_list("radical_id", flat=True)
        radical_qs = Radical.objects.filter(pk__in=radical_ids)

        return RadicalSerializer(radical_qs, many=True, context=self.context).data

    def _get_input_text(self, instance):
        assert isinstance(instance, Logogram)

        return instance.id
