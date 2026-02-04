#!/usr/bin/env bash
# Single-container entrypoint: start Postgres (if no DATABASE_URL), Redis, migrate, Celery, Daphne.
set -e
cd /app

export PGPASSWORD="${POSTGRES_PASSWORD:-skillspot}"

# Start in-container Postgres only when not using external DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
  echo "==> Starting PostgreSQL..."
  PGVERSION=$(ls /usr/lib/postgresql 2>/dev/null | head -1)
  if [ -n "$PGVERSION" ]; then
    sudo -u postgres "/usr/lib/postgresql/$PGVERSION/bin/pg_ctl" -D /var/lib/postgresql/data -l /tmp/pg.log -w start
  fi
  until pg_isready -U postgres -h 127.0.0.1 2>/dev/null; do
    sleep 1
  done
  # Ensure user and DB exist (idempotent)
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER:-skillspot}'" | grep -q 1 || \
    sudo -u postgres createuser -s "${POSTGRES_USER:-skillspot}" 2>/dev/null || true
  sudo -u postgres psql -c "ALTER USER ${POSTGRES_USER:-skillspot} WITH PASSWORD '${POSTGRES_PASSWORD:-skillspot}';" 2>/dev/null || true
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB:-skillspot}'" | grep -q 1 || \
    sudo -u postgres createdb -O "${POSTGRES_USER:-skillspot}" "${POSTGRES_DB:-skillspot}" 2>/dev/null || true
  echo "==> PostgreSQL ready."
else
  echo "==> Using external DATABASE_URL (skipping in-container Postgres)."
fi

# Start Redis (in-container)
echo "==> Starting Redis..."
redis-server --daemonize yes
until redis-cli ping 2>/dev/null | grep -q PONG; do
  sleep 1
done
echo "==> Redis ready."

# Migrations
echo "==> Running migrations..."
python3 manage.py migrate --noinput

# Collect static files (admin CSS, etc.)
echo "==> Collecting static files..."
python3 manage.py collectstatic --noinput

# Create superuser if env vars set (idempotent; skips if user exists). Use with persistent DB or re-run on each deploy.
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ]; then
  echo "==> Creating superuser (if not exists)..."
  python3 manage.py createsuperuser --noinput 2>/dev/null || true
fi

# Celery in background
echo "==> Starting Celery worker..."
celery -A skillspot worker -l info &
CELERY_PID=$!
trap "kill $CELERY_PID 2>/dev/null" EXIT

# Daphne (Render sets PORT)
PORT="${PORT:-8000}"
echo "==> Starting Daphne on 0.0.0.0:$PORT..."
exec daphne -b 0.0.0.0 -p "$PORT" skillspot.asgi:application



