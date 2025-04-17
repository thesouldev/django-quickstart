#!/bin/bash

# Source environment variables with proper error handling
set -a
if [ -f /scripts/.env ]; then
    . /scripts/.env
    echo "Loaded environment variables from .env"
else
    echo "Warning: .env file not found."
fi
set +a

# Check if required variables are set
if [ -z "$DJANGO_DB_NAME" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$DJANGO_DB_HOST" ] || [ -z "$DJANGO_DB_PORT" ]; then
    echo "Error: One or more required database environment variables are not set."
    echo "Required variables: DJANGO_DB_NAME, POSTGRES_PASSWORD, DJANGO_DB_HOST, DJANGO_DB_PORT"
    exit 1
fi

echo "Dropping database $DJANGO_DB_NAME..."

# Terminate existing connections
echo "Terminating existing connections to $DJANGO_DB_NAME..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DJANGO_DB_HOST" -p "$DJANGO_DB_PORT" -U postgres -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DJANGO_DB_NAME' AND pid <> pg_backend_pid();"

# Drop the database with error handling
echo "Attempting to drop database $DJANGO_DB_NAME..."
if PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DJANGO_DB_HOST" -p "$DJANGO_DB_PORT" -U postgres -d postgres -c "DROP DATABASE IF EXISTS $DJANGO_DB_NAME;"; then
    echo "Database $DJANGO_DB_NAME dropped successfully."
else
    echo "Error: Failed to drop database $DJANGO_DB_NAME. Check your credentials and permissions."
    exit 1
fi

# Optional: recreate the database
# Uncomment if you want to automatically recreate the database
# echo "Creating database $DJANGO_DB_NAME..."
# if PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$DJANGO_DB_HOST" -p "$DJANGO_DB_PORT" -U "$DJANGO_DB_USER" -d postgres -c "CREATE DATABASE $DJANGO_DB_NAME;"; then
#     echo "Database $DJANGO_DB_NAME created successfully."
# else
#     echo "Error: Failed to create database $DJANGO_DB_NAME."
#     exit 1
# fi