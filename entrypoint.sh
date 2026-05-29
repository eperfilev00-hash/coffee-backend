#!/bin/sh
set -e

echo "Running migrations..."
cd /app/coffee_backend
alembic upgrade head

echo "Starting application..."
exec uvicorn coffee_backend.app.main:app --host 0.0.0.0 --port 8000