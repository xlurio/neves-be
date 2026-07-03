# noqa: INP001

import os
import pathlib
import sys

from nncf import CompressWeightsMode

BASE_URL = pathlib.Path(__file__).parent.parent

sys.path.append(str(BASE_URL))
assert pathlib.Path(BASE_URL / "config" / "settings" / "local.py").is_file()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django  # noqa: E402

django.setup()

from neves_be.genai.services.qwen_3_tts_helper import convert_qwen3_tts_model  # noqa: E402, I001
from django.conf import settings  # noqa: E402


def main():
    convert_qwen3_tts_model(
        model_id="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        output_dir=settings.GENAI_TTS_MODEL_PATH,
        quantization_config={"mode": CompressWeightsMode.INT8_SYM},
    )


if __name__ == "__main__":
    main()
