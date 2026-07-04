from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import serializers

from neves_be.common.serializers import CamelCaseAliasSerializerMixin
from neves_be.genai.services.text2speech import generate_speech
from neves_be.genai.services.translation import generate_translation
from neves_be.lang_model.serializers import PronounceOrGenerateMixin
from neves_be.lang_model.serializers import PronounceOrGenerateMixinCtx
from neves_be.word_lm.models import Ngram
from neves_be.word_lm.models import Sentence
from neves_be.word_lm.models import Word

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from rest_framework.fields import Field


class SentenceSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
    context: PronounceOrGenerateMixinCtx

    meaning = serializers.SerializerMethodField()
    pronounce = serializers.SerializerMethodField()

    class Meta:
        model = Sentence
        fields = ["id", "value"]

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)

    def get_meaning(self, instance: Sentence) -> str:
        return generate_translation(instance.value)

    def get_pronounce(self, instance: Sentence) -> str:
        return self.context["request"].build_absolute_uri(
            generate_speech(instance.value),
        )


class NgramSerializer(CamelCaseAliasSerializerMixin, serializers.ModelSerializer):
    meaning = serializers.SerializerMethodField()
    pronounce = serializers.SerializerMethodField()

    class Meta:
        model = Ngram
        fields = ["id", "value", "n_words", "occurrences", "meaning", "pronounce"]

    camel_case_aliases = {
        "n_words": "nWords",
    }

    def get_fields(self) -> MutableMapping[str, Field]:
        fields = super().get_fields()
        return self._rename_camel_case_fields(fields)

    def get_meaning(self, instance: Ngram) -> str:
        return generate_translation(instance.value)

    def get_pronounce(self, instance: Sentence) -> str:
        return self.context["request"].build_absolute_uri(
            generate_speech(instance.value),
        )


class WordSerializer(
    CamelCaseAliasSerializerMixin,
    serializers.ModelSerializer,
    PronounceOrGenerateMixin,
):
    pronounce = serializers.SerializerMethodField()
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ["id", "value", "pronounce", "meaning"]

    def get_meaning(self, instance: Ngram) -> str:
        return generate_translation(instance.value)

    def _get_input_text(self, instance):
        assert isinstance(instance, Word)

        return instance.value
