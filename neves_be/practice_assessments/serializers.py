from collections.abc import MutableMapping
from typing import assert_never

from rest_framework import serializers
from rest_framework.fields import Field

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.practice_assessments.models import RadicalSessionAssessment
from neves_be.practice_assessments.models import SentenceSessionAssessment
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestion
from neves_be.practice_questions.models import PracticeSessionAssessmentQuestionAlt
from neves_be.practice_sessions.types import SessionType


class RadicalSessionAssessmentSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "finished_at": "finishedAt",
    }

    class Meta:
        model = RadicalSessionAssessment
        fields = ["id", "finished_at", "score"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


class SentenceSessionAssessmentSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "finished_at": "finishedAt",
    }

    class Meta:
        model = SentenceSessionAssessment
        fields = ["id", "finished_at", "score"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


def make_practice_assessment_srlr_cls(
    session_type: SessionType,
) -> type[serializers.Serializer]:
    if session_type == "radicals":
        return RadicalSessionAssessmentSerializer

    if session_type == "sentences":
        return SentenceSessionAssessmentSerializer

    assert_never(session_type)


class PracticeQuestionAltSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSessionAssessmentQuestionAlt
        fields = {"letter", "type", "payload"}


class PracticeQuestionSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
):
    camel_case_aliases = {
        "curr_answer": "currAnswer",
    }
    alternatives = PracticeQuestionAltSerializer(many=True)

    class Meta:
        model = PracticeSessionAssessmentQuestion
        fields = {"id", "type", "question", "audio", "alternatives", "currAnswer"}

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)


class PracticeQuestionResultSerializer(PracticeQuestionSerializer):
    camel_case_aliases = {
        **PracticeQuestionSerializer.camel_case_aliases,
        "expected_answer": "expectedAnswer",
    }

    class Meta(PracticeQuestionSerializer.Meta):
        fields = {*PracticeQuestionSerializer.Meta.fields, "expected_answer"}
