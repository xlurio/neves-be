from __future__ import annotations

from typing import ClassVar

from rest_framework import serializers

from neves_be.radicals.models import Radical
from neves_be.radicals.models import RadicalSession
from neves_be.radicals.models import RadicalSessionTest
from neves_be.radicals.models import RadicalSessionTestQuestion


class CamelCaseAliasSerializerMixin:
    camel_case_aliases: ClassVar[dict[str, str]] = {}

    def _rename_camel_case_fields(self, fields):
        for snake_case_name, camel_case_name in self.camel_case_aliases.items():
            fields[camel_case_name] = fields.pop(snake_case_name)
        return fields


class UserCreateResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()


class UserStatisticsSerializer(CamelCaseAliasSerializerMixin, serializers.Serializer):
    chinese_logographic_system = serializers.DictField(
        child=serializers.FloatField(),
    )
    camel_case_aliases = {
        "chinese_logographic_system": "chineseLogographicSystem",
    }

    def get_fields(self):
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


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

    def get_fields(self):
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

        if instance.pronounce.startswith("http://") or instance.pronounce.startswith(
            "https://",
        ):
            return instance.pronounce

        request = self.context.get("request")
        if request is not None and instance.pronounce.startswith("/"):
            return request.build_absolute_uri(instance.pronounce)

        return instance.pronounce


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

    def get_fields(self):
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


class RadicalSessionTestQuestionResultSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "curr_answer": "currAnswer",
        "expected_answer": "expectedAnswer",
    }

    class Meta:
        model = RadicalSessionTestQuestion
        fields = [
            "type",
            "question",
            "alternatives",
            "curr_answer",
            "expected_answer",
            "audio",
        ]

    def get_fields(self):
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)
