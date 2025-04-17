#!/bin/sh

set -a
[ -f /app/.env ] && . /app/.env
set +a

if [ "$ENVIRONMENT" = "local" ]; then
  # Wait for PostgreSQL to be available
  until pg_isready -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER; do
    echo "Waiting for PostgreSQL..."
    sleep 1
  done

  # Check if the database user exists and create if it doesn't
  echo "Checking if the database user $DJANGO_DB_USER exists..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DJANGO_DB_USER'" | grep -q 1
  if [ $? -ne 0 ]; then
    echo "Database user $DJANGO_DB_USER does not exist. Creating..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "CREATE USER $DJANGO_DB_USER WITH PASSWORD '$DJANGO_DB_PASSWORD';"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "ALTER ROLE $DJANGO_DB_USER SET client_encoding TO 'utf8';"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "ALTER ROLE $DJANGO_DB_USER SET default_transaction_isolation TO 'read committed';"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "ALTER ROLE $DJANGO_DB_USER SET timezone TO 'UTC';"
    echo "Database user $DJANGO_DB_USER created successfully."
  else
    echo "Database user $DJANGO_DB_USER already exists."
  fi

  # Create the database if it does not exist
  echo "Checking if the database $DJANGO_DB_NAME exists..."
  PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DJANGO_DB_NAME'" | grep -q 1
  if [ $? -ne 0 ]; then
    echo "Database $DJANGO_DB_NAME does not exist. Creating..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $DJANGO_DB_NAME"
    
    # Grant privileges to Django DB user on the new database
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DJANGO_DB_NAME TO $DJANGO_DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "ALTER USER $DJANGO_DB_USER CREATEDB;"
    
    # Grant privileges on the public schema - CRITICAL for PostgreSQL 15+
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "GRANT ALL ON SCHEMA public TO $DJANGO_DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DJANGO_DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DJANGO_DB_USER;"
  else
    echo "Database $DJANGO_DB_NAME already exists."
    
    # Ensure Django DB user has proper permissions on existing database
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DJANGO_DB_NAME TO $DJANGO_DB_USER;"
    
    # Grant privileges on the public schema - CRITICAL for PostgreSQL 15+
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "GRANT ALL ON SCHEMA public TO $DJANGO_DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DJANGO_DB_USER;"
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DJANGO_DB_HOST -p $DJANGO_DB_PORT -U $POSTGRES_USER -d $DJANGO_DB_NAME -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DJANGO_DB_USER;"
  fi
fi

# Apply database migrations
echo "Applying database migrations..."
poetry run python manage.py migrate

if [ "$ENVIRONMENT" = "local" ]; then
  # Create superuser if it doesn't exist
  echo "Creating superuser if it doesn't exist..."
  poetry run python manage.py createsu
fi

export PYTHONPATH="/app/src:$PYTHONPATH"
exec "$@"