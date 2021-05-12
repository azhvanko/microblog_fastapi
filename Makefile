API_CONTAINER=fastapi_microblog_api_dev
ALEMBIC_MAKE_MIGRATION_COMMAND="cd ./app/database && alembic revision --autogenerate -m \"$(message)\""
ALEMBIC_MIGRATE_COMMAND="cd ./app/database && alembic upgrade head"


start:
	docker-compose -f docker-compose.dev.yml up

build:
	docker-compose -f docker-compose.dev.yml up --build

make_migration:
	docker exec -it $(API_CONTAINER) sh -c $(ALEMBIC_MAKE_MIGRATION_COMMAND)

migrate:
	docker exec -it $(API_CONTAINER) sh -c $(ALEMBIC_MIGRATE_COMMAND)

test:
	docker exec -it $(API_CONTAINER) sh -c "pytest -v"
