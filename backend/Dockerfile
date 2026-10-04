# App image only — Postgres and Redis are external (compose locally, hosted in prod).
# Build: docker build -t skillspot .
# Local:  docker compose up --build
# Prod:   docker run -p 8000:8000 -e SECRET_KEY=... -e DATABASE_URL=... -e REDIS_URL=... skillspot

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Runtime libs for psycopg2-binary / Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static at build time (Whitenoise serves from STATIC_ROOT).
# Dummy SECRET_KEY is enough; collectstatic does not need a real database.
RUN SECRET_KEY=build-time-only \
    DEBUG=False \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runapp"]
