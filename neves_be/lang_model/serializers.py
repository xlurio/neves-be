from typing import TypedDict

from django.http import HttpRequest
from rest_framework import serializers

from neves_be.char_lm.models import Logogram
from neves_be.genai.services.text2speech import generate_speech


class PronounceOrGenerateMixinCtx(TypedDict):
    request: HttpRequest


class PronounceOrGenerateMixin:
    context: PronounceOrGenerateMixinCtx

    pronounce = serializers.SerializerMethodField()

    def get_pronounce(self, instance: Logogram) -> str:
        if not instance.pronounce:
            return generate_speech(instance.id)

        if instance.pronounce.startswith(("http://", "https://")):
            return instance.pronounce

        if instance.pronounce.startswith("/"):
            return self.context["request"].build_absolute_uri(instance.pronounce)

        return instance.pronounce
