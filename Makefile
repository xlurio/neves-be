dockercompose=docker compose -f docker-compose.local.yml
dockercomposeup=$(dockercompose) up -d

build:
	$(dockercompose) build

down:
	$(dockercompose) down -v

import_mcc2lm:
	$(dockercompose) run --rm django sh -c 'python manage.py import_mcc2lm mcc2lm.db'

logscelery:
	$(dockercompose) logs -fn200 celery

logsdjango:
	$(dockercompose) logs -fn200 django

logspostgres:
	$(dockercompose) logs -fn200 postgres

logsrabbitmq:
	$(dockercompose) logs -fn200 rabbitmq

migrate:
	$(dockercompose) run --rm django sh -c 'python manage.py migrate'

pull:
	$(dockercompose) pull

stop:
	$(dockercompose) stop

stopcelery:
	$(dockercompose) stop celery

stopcelerydjango:
	$(dockercompose) stop celery django

stopdjango:
	$(dockercompose) stop django

stoprabbitmq:
	$(dockercompose) stop rabbitmq

up:
	$(dockercomposeup)

upbuild:
	$(dockercomposeup) --build

uppostgres:
	$(dockercomposeup) postgres
