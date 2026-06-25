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
    main_representation = serializers.SerializerMethodField()
    other_vars = serializers.SerializerMethodField()
    pronounce = serializers.SerializerMethodField()
    camel_case_aliases = {
        "main_representation": "mainRepresentation",
        "other_vars": "otherVars",
    }

    class Meta:
        model = Radical
        fields = [
            "id",
            "main_representation",
            "other_vars",
            "pinyin",
            "meaning",
            "pronounce",
        ]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)

    def get_main_representation(self, instance: Radical) -> int:
        if instance.main_representation is not None:
            return instance.main_representation
        return ord(instance.id[0]) if instance.id else 0

    def get_other_vars(self, instance: Radical) -> list[int]:
        if isinstance(instance.other_vars, list):
            return [int(value) for value in instance.other_vars]
        return []

    def get_pronounce(self, instance: Radical) -> str:
        if not instance.pronounce:
            return ""
        if instance.pronounce.startswith(("http://", "https://")):
            return instance.pronounce

        typed_request = cast("Request | None", self.context.get("request"))
        if typed_request is not None and instance.pronounce.startswith("/"):
            return typed_request.build_absolute_uri(instance.pronounce)
        return instance.pronounce
