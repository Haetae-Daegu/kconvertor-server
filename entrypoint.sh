#!/bin/bash
set -e

sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}|" alembic.ini

echo "Waiting for PostgreSQL..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  echo "PostgreSQL is not available - waiting..."
  sleep 3
done

echo "PostgreSQL is available"

PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "
DROP TABLE IF EXISTS alembic_version;
"

echo "Creating tables"
python -c "
from app import create_app
from app.database.database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Tables created successfully!')
"

echo "Stamp migrations"
alembic stamp head

echo "Starting Flask application..."
flask run --host=0.0.0.0 