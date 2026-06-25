#! /bin/bash

set -xe

.venv/bin/mypy .
.venv/bin/ruff format .
.venv/bin/ruff check .
caustin --suffix '.py' --exclude='.venv' --exclude='manage.py' \
    --exclude='tests' --exclude='**/migrations/*.py' --exclude='config'
git add . && .venv/bin/pre-commit run --all
docker compose -f docker-compose.local.yml run --rm django sh -c 'pytest'
