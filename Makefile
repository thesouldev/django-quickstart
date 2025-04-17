.PHONY: build run

set:set-gcloud-project set-env

set-gcloud-project:
	@bash scripts/manage.sh set-gcloud-project

build:
	docker-compose build --no-cache

run:
	docker-compose up

format:
	docker-compose exec web poetry run isort .
	docker-compose exec web poetry run black .

lint:
	docker-compose exec web poetry run flake8 .

type-check:
	docker-compose exec web poetry run pyre check

dropdb:
	docker-compose exec db /scripts/drop_db.sh

migrate:
	docker-compose exec web poetry run python manage.py migrate

makemigrations:
	docker-compose exec web poetry run python manage.py makemigrations

update-env:
	@bash scripts/manage.sh update-env

set-env:
	@bash scripts/manage.sh set-env

deploy:
	@bash scripts/manage.sh deploy

coverage:
	docker-compose exec web poetry run coverage run ./manage.py test
	docker-compose exec web poetry run coverage report
	docker-compose exec web poetry run coverage html
