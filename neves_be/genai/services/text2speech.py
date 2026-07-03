from __future__ import annotations

import functools
import logging
import pathlib
import tempfile

import soundfile as sf
from django.core.files.base import File
from django.db import transaction

from neves_be.genai.models import GeneratedSpeech
from neves_be.genai.services.qwen_3_tts_helper import OVQwen3TTSModel
from neves_be.practice_assessments.constants import MASK_TOKEN

_logger = logging.getLogger(__name__)


@functools.cache
def make_tts_model():
    assert pathlib.Path(
        "/app/tts_model/speech_tokenizer/model.safetensors",
    ).is_file()
    return OVQwen3TTSModel.from_pretrained("/app/tts_model", device="CPU")


@transaction.atomic
def generate_speech(txt: str) -> str:
    if audio_model := GeneratedSpeech.objects.filter(id=hash(txt)).first():
        return audio_model.audio.url

    _logger.info("No speech was found for '%s', generating a new one", txt)

    wavs, sr = make_tts_model().generate_voice_clone(
        text=txt.replace(MASK_TOKEN, "…"),
        language="Chinese",
        ref_audio="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/clone_2.wav",
        ref_text="甚至出现交易几乎停滞的情况。",
    )

    audio_model, _ = GeneratedSpeech.objects.get_or_create(id=hash(txt))

    with tempfile.NamedTemporaryFile("w+b", suffix=".wav") as audio_file:
        sf.write(audio_file.name, wavs[0], sr)
        audio_model.audio.save(f"speech_{audio_model.id}.wav", content=File(audio_file))

    assert audio_model.audio.name

    return audio_model.audio.url
