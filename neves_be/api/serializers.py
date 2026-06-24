from __future__ import annotations

from rest_framework import serializers

from neves_be.radicals.models import Radical
from neves_be.radicals.models import RadicalSession
from neves_be.radicals.models import RadicalSessionTest
from neves_be.radicals.models import RadicalSessionTestQuestion


class UserCreateResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()


class UserStatisticsSerializer(serializers.Serializer):
    chineseLogographicSystem = serializers.DictField(child=serializers.FloatField())


class RadicalSessionSerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at")
    numOfRadicals = serializers.IntegerField(source="num_of_radicals")
    highestScore = serializers.IntegerField(source="highest_score")

    class Meta:
        model = RadicalSession
        fields = ["id", "createdAt", "numOfRadicals", "highestScore"]


class RadicalSerializer(serializers.ModelSerializer):
    mainRepresentation = serializers.SerializerMethodField()
    otherVars = serializers.SerializerMethodField()
    pronounce = serializers.SerializerMethodField()

    class Meta:
        model = Radical
        fields = [
            "id",
            "mainRepresentation",
            "otherVars",
            "pinyin",
            "meaning",
            "pronounce",
        ]

    def get_mainRepresentation(self, instance: Radical) -> int:
        if instance.main_representation is not None:
            return instance.main_representation
        return ord(instance.id[0]) if instance.id else 0

    def get_otherVars(self, instance: Radical) -> list[int]:
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


class RadicalSessionTestSerializer(serializers.ModelSerializer):
    finishedAt = serializers.DateTimeField(source="finished_at", allow_null=True)

    class Meta:
        model = RadicalSessionTest
        fields = ["id", "finishedAt", "score"]


class RadicalSessionTestQuestionResultSerializer(serializers.ModelSerializer):
    currAnswer = serializers.CharField(source="curr_answer")
    expectedAnswer = serializers.CharField(source="expected_answer")

    class Meta:
        model = RadicalSessionTestQuestion
        fields = [
            "type",
            "question",
            "alternatives",
            "currAnswer",
            "expectedAnswer",
            "audio",
        ]
