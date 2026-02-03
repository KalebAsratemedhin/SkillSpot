#!/usr/bin/env bash
# Start everything: Docker (Postgres + Redis), Celery worker, and Django server.
# Run from project root: ./server/start.sh   OR from server: ./start.sh

set -e
cd "$(dirname "$0")"

echo "==> Starting Docker (Postgres + Redis)..."
docker compose up -d

echo "==> Waiting for Postgres to be ready..."
for i in {1..30}; do
  if docker compose exec -T db pg_isready -U skillspot -d skillspot 2>/dev/null; then
    break
  fi
  sleep 1
done

echo "==> Waiting for Redis to be ready..."
for i in {1..30}; do
  if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    break
  fi
  sleep 1
done

echo "==> Starting Celery worker in background..."
source venv/bin/activate
celery -A skillspot worker -l info &
CELERY_PID=$!
trap "kill $CELERY_PID 2>/dev/null" EXIT

echo "==> Starting Django (Daphne for HTTP + WebSocket)..."
daphne -b 127.0.0.1 -p 8000 skillspot.asgi:application

