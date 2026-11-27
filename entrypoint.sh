#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  echo "PostgreSQL is not available - waiting..."
  sleep 3
done

echo "PostgreSQL is available"

# Safety net for the one-time switch to Alembic: an existing database that was
# never stamped must not go through "upgrade head", which would try to recreate
# the tables. See docs/RUNBOOK.md, "Database migrations".
q() { PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -tAc "$1"; }
HAS_TABLES=$(q "SELECT to_regclass('public.users') IS NOT NULL")
HAS_VERSION=$(q "SELECT to_regclass('public.alembic_version') IS NOT NULL")
VERSION_ROWS=0
if [ "$HAS_VERSION" = "t" ]; then
  VERSION_ROWS=$(q "SELECT count(*) FROM alembic_version")
fi
if [ "$HAS_TABLES" = "t" ] && [ "$VERSION_ROWS" = "0" ]; then
  echo "ERROR: tables exist but the database is not stamped by Alembic."
  echo "Run once: docker compose run --rm --entrypoint alembic app stamp 0001_baseline"
  exit 1
fi

echo "Applying migrations"
alembic upgrade head

echo "Starting Flask application..."
flask run --host=0.0.0.0
