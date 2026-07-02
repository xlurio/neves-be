from typing import TYPE_CHECKING
from typing import cast

from rest_framework import serializers

from neves_be.char_lm.models import Logogram
from neves_be.genai.services.text2speech import generate_speech

if TYPE_CHECKING:
    from rest_framework.request import Request


class PronounceOrGenerateMixin:
    pronounce = serializers.SerializerMethodField()

    def get_pronounce(self, instance: Logogram) -> str:
        if not instance.pronounce:
            return generate_speech(instance.id)

        if instance.pronounce.startswith(("http://", "https://")):
            return instance.pronounce

        typed_request = cast("Request | None", self.context.get("request"))

        if typed_request is not None and instance.pronounce.startswith("/"):
            return typed_request.build_absolute_uri(instance.pronounce)

        return instance.pronounce
