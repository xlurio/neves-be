#! /bin/bash

set -xe

.venv/bin/ruff format .
# .venv/bin/mypy . --show-traceback --exclude 'neves_be/practice_assessments/services/sentences.py'
.venv/bin/ruff check . --fix --unsafe-fixes
.venv/bin/pylint --disable=all --enable=similarities --recursive=y \
    --ignore '.venv,manage.py,tests,config' --ignore-paths '.*/migrations/.*' .
caustin --suffix '.py' --exclude='.venv' --exclude='manage.py' \
    --exclude='tests' --exclude='**/migrations/*.py' --exclude='config'
git add . && .venv/bin/pre-commit run --all
docker compose -f docker-compose.local.yml run --rm django sh -c 'pytest'
