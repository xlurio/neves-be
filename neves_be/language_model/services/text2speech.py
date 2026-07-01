from __future__ import annotations

import functools
import tempfile

import soundfile as sf
import torch
from django.core.files.base import File
from qwen_tts import Qwen3TTSModel

from neves_be.language_model.models import GeneratedSpeech
from neves_be.practice_assessments.constants import MASK_TOKEN


@functools.cache
def make_tts_model():
    return Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        device_map="cuda:0",
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )


def generate_speech(text: str) -> str:
    if audio_model := GeneratedSpeech.objects.get(id=hash(text)):
        return audio_model.audio.url

    wavs, sr = make_tts_model().generate_voice_clone(
        text=text.replace(MASK_TOKEN, "…"),
        language="Chinese",
        ref_audio="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/clone_2.wav",
        ref_text="甚至出现交易几乎停滞的情况。",
    )

    audio_model = GeneratedSpeech.objects.create(id=hash(text))

    with tempfile.NamedTemporaryFile("w+") as audio_file:
        sf.write(audio_file.name, wavs[0], sr)
        audio_model.audio.save(content=File(audio_file))

    return audio_model.audio.url
