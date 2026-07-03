#! /bin/bash

set -xe

.venv/bin/ruff format .
.venv/bin/mypy . --show-traceback --exclude '^translation_model' \
    --exclude '^tts_model' --exclude '^config' --exclude 'qwen_3_tts_helper.py'
.venv/bin/ruff check . --fix --unsafe-fixes
# .venv/bin/pylint --disable=all --enable=similarities --recursive=y \
#     --ignore '.venv,manage.py,tests,translation_model,tts_model,config,qwen_3_tts_helper.py' \
#     --ignore-paths '.*/migrations/.*' .
caustin --suffix '.py' --exclude='.venv' --exclude='manage.py' \
    --exclude='tests' --exclude='**/migrations/*.py' --exclude='config' \
    --exclude='qwen_3_tts_helper.py' --exclude='tts_model' \
    --exclude='translation_model' --max-lines 300
git add . && .venv/bin/pre-commit run --all
docker compose -f docker-compose.local.yml run --rm django sh -c 'pytest tests'
