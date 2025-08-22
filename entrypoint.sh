#!/bin/sh

while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

alembic upgrade head

uvicorn main:app --host "0.0.0.0" --port 8000