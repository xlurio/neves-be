dockercompose=docker compose -f docker-compose.local.yml
dockercomposeup=$(dockercompose) up -d

migrate:
	$(dockercompose) run --rm django sh -c 'python manage.py migrate'

up:
	$(dockercomposeup)

uppostgres:
	$(dockercomposeup) postgres
