from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.radicals.models import Radical

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
