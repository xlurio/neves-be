#! /bin/bash

set -xe

uv run optimum-cli export openvino --model facebook/nllb-200-distilled-600M \
  --task text2text-generation-with-past --weight-format int8 translation_model

uv run huggingface-cli download Echo9Zulu/Qwen3-TTS-12Hz-Base-1.7B-INT8-OpenVINO \
  --local-dir ./tts_model

cd tts_model/speech_tokenizer && \
  wget https://huggingface.co/Qwen/Qwen3-TTS-Tokenizer-12Hz/resolve/main/model.safetensors
