from __future__ import annotations

import abc
from typing import TYPE_CHECKING
from typing import Any
from typing import TypedDict

from neves_be.genai.services.text2speech import generate_speech

if TYPE_CHECKING:
    from django.http import HttpRequest

    class WithPronounceCls:
        pronounce: str


class PronounceOrGenerateMixinCtx(TypedDict):
    request: HttpRequest


class PronounceOrGenerateMixin:
    context: PronounceOrGenerateMixinCtx

    def get_pronounce(self, instance: WithPronounceCls) -> str:
        if not instance.pronounce:
            return self.context["request"].build_absolute_uri(
                generate_speech(self._get_input_text(instance)),
            )

        if instance.pronounce.startswith(("http://", "https://")):
            return instance.pronounce

        if instance.pronounce.startswith("/"):
            return self.context["request"].build_absolute_uri(instance.pronounce)

        msg = f"Invalid word pronounce audio path: {instance.pronounce}"
        raise ValueError(msg)

    @abc.abstractmethod
    def _get_input_text(self, instance: Any) -> str:
        raise NotImplementedError
