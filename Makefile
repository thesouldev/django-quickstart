.PHONY: build run

set:set-gcloud-project set-env

set-gcloud-project:
	@bash scripts/manage.sh set-gcloud-project

build:
	docker-compose build --no-cache

run:
	docker-compose up

format:
	docker-compose run --rm --entrypoint="" web poetry run isort .
	docker-compose run --rm --entrypoint="" web poetry run black .

lint:
	docker-compose run --rm --entrypoint="" web poetry run flake8 .

type-check:
	docker-compose run --rm --entrypoint="" web poetry run pyre check

dropdb:
	docker-compose run --rm --entrypoint="" db /scripts/drop_db.sh

db-migrate:
	docker-compose run --rm --entrypoint="" web poetry run python src/manage.py migrate

db-generate:
	docker-compose run --rm --entrypoint="" web poetry run python src/manage.py makemigrations

shell:
	docker-compose run --rm --entrypoint="" web poetry run python src/manage.py shell_plus

down:
	docker-compose down -v
update-env:
	@bash scripts/manage.sh update-env

set-env:
	@bash scripts/manage.sh set-env

deploy:
	@bash scripts/manage.sh deploy

coverage:
	docker-compose run --rm --entrypoint="" web poetry run coverage run ./src/manage.py test
	docker-compose run --rm --entrypoint="" web poetry run coverage report
	docker-compose run --rm --entrypoint="" web poetry run coverage html