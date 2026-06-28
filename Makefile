dockercompose=docker compose -f docker-compose.local.yml
dockercomposeup=$(dockercompose) up -d

build:
	$(dockercompose) build

down:
	$(dockercompose) down -v

logsdjango:
	$(dockercompose) logs -fn200 django

migrate:
	$(dockercompose) run --rm django sh -c 'python manage.py migrate'

stop:
	$(dockercompose) stop

up:
	$(dockercomposeup)

upbuild:
	$(dockercomposeup) --build

uppostgres:
	$(dockercomposeup) postgres
