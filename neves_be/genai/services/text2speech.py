from __future__ import annotations

import functools
import logging
import tempfile

import soundfile as sf
from django.core.files.base import File
from django.db import transaction

from neves_be.genai.models import GeneratedSpeech
from neves_be.genai.services.local_utils import generation_cache_id
from neves_be.genai.services.qwen_3_tts_helper import OVQwen3TTSModel

_logger = logging.getLogger(__name__)

_OV_MODEL_DIR = "tts_model"


@functools.cache
def make_tts_model():
    return OVQwen3TTSModel.from_pretrained(_OV_MODEL_DIR, device="CPU")


@transaction.atomic
def generate_speech(txt: str) -> str:
    if audio_model := GeneratedSpeech.objects.filter(
        id=generation_cache_id(txt),
    ).first():
        return audio_model.audio.url

    _logger.info("No speech was found for '%s', generating a new one", txt)

    wavs, sr = make_tts_model().generate_custom_voice(
        text=txt,
        speaker="serena",
        language="Chinese",
        max_new_tokens=4096,
    )

    audio_model, _ = GeneratedSpeech.objects.get_or_create(id=hash(txt))

    with tempfile.NamedTemporaryFile("w+b", suffix=".wav") as audio_file:
        sf.write(audio_file.name, wavs[0], sr)
        audio_model.audio.save(f"speech_{audio_model.id}.wav", content=File(audio_file))

    assert audio_model.audio.name

    return audio_model.audio.url
