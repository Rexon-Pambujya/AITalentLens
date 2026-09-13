#!/bin/sh
# Combined API + Celery worker entrypoint for the free-tier deploy (Render).
#
# Render's free plan only grants one always-on-ish service, with no
# "Background Worker" service type (that requires a paid plan) - so this
# script runs the Celery worker as a background process inside the same
# container as the API instead of as a separate service. Local dev is
# unaffected: infra/docker-compose.yml still runs api/worker as two
# containers and does not use this script.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Celery worker in background..."
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 &

echo "Starting API server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
