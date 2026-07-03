#! /bin/bash

set -x

mkdir -p ./.local_tmp

set -e

export TMPDIR=$(pwd)/.local_tmp
export TEMP=$(pwd)/.local_tmp
export TMP=$(pwd)/.local_tmp

TTS_MODEL_PATH=./tts_model

uv run optimum-cli export openvino --model facebook/nllb-200-distilled-600M \
  --task text2text-generation-with-past --weight-format int8 translation_model

if [ -d "$TTS_MODEL_PATH/.git" ]; then
  git -C "$TTS_MODEL_PATH" pull --ff-only
else
  rm -rf "$TTS_MODEL_PATH"
  git clone git@github.com:QwenLM/Qwen3-TTS.git "$TTS_MODEL_PATH"
fi

DATABASE_URL=sqlite:///:memory: \
  uv run python scripts/convertqwenttstoopenvino.py

set +e

unset TMPDIR
unset TEMP
unset TMP

rm -rf ./.local_tmp
