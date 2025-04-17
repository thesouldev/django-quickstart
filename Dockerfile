FROM python:3.12

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y postgresql-client gcc python3-dev libpq-dev

RUN mkdir /app

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml poetry.lock* /app/

RUN poetry install

COPY . /app/

WORKDIR /app/src

RUN chmod +x /app/entrypoint.sh /app/scripts/drop_db.sh

RUN poetry run python manage.py collectstatic --noinput

ENTRYPOINT ["/app/entrypoint.sh"]
