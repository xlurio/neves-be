from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.language_model.models import Logogram
from neves_be.language_model.models import Radical
from neves_be.language_model.models import Sentence
from neves_be.language_model.models import Word

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from rest_framework.fields import Field
    from rest_framework.request import Request


class RadicalSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
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

    def get_pronounce(self, instance: Radical) -> str:
        if not instance.pronounce:
            return ""
        if instance.pronounce.startswith(("http://", "https://")):
            return instance.pronounce

        typed_request = cast("Request | None", self.context.get("request"))
        if typed_request is not None and instance.pronounce.startswith("/"):
            return typed_request.build_absolute_uri(instance.pronounce)
        return instance.pronounce


class SentenceSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Sentence
        fields = ["id", "value"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


class WordSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ["id", "value"]


class LogogramSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Logogram
        fields = ["id", "pinyin", "meaning"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()

        return self._rename_camel_case_fields(fields)

    def get_radicals(self, instance: Logogram) -> list[dict[str, Any]]:
        radical_ids = instance.logogram_radicals.values_list("logogram_id", flat=True)
        radical_qs = Radical.objects.filter(pk__in=radical_ids)

        return RadicalSerializer(radical_qs, many=True)
