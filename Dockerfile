FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y postgresql-client gcc python3-dev libpq-dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - 

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN mkdir /app

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh /app/scripts/drop_db.sh

RUN poetry run python src/manage.py collectstatic --noinput

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]