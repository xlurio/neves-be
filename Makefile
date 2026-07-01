dockercompose=docker compose -f docker-compose.local.yml
dockercomposeup=$(dockercompose) up -d

build:
	$(dockercompose) build

down:
	$(dockercompose) down -v

import_mcc2lm:
	$(dockercompose) run --rm django sh -c 'python manage.py import_mcc2lm mcc2lm.db'

logsdjango:
	$(dockercompose) logs -fn200 django

migrate:
	$(dockercompose) run --rm django sh -c 'python manage.py migrate'

pull:
	$(dockercompose) pull

stop:
	$(dockercompose) stop

stopdjango:
	$(dockercompose) stop django

up:
	$(dockercomposeup)

upbuild:
	$(dockercomposeup) --build

uppostgres:
	$(dockercomposeup) postgres
