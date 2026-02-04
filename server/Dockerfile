# Single-container image: Django app + in-container PostgreSQL + Redis.
# Set DATABASE_URL to use an external Postgres provider instead of in-container Postgres.
# Build from server/: docker build -t skillspot .
# Run: docker run -p 8000:8000 -e SECRET_KEY=xxx skillspot
# With external DB: docker run -p 8000:8000 -e SECRET_KEY=xxx -e DATABASE_URL=postgres://... skillspot

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install Python, PostgreSQL, Redis, and deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    postgresql \
    postgresql-client \
    redis-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Initialize Postgres cluster so entrypoint can start it (no systemd in container)
# Ubuntu postgresql package puts binaries in /usr/lib/postgresql/<version>/bin
RUN mkdir -p /var/run/postgresql /var/lib/postgresql/data \
    && chown -R postgres:postgres /var/run/postgresql /var/lib/postgresql \
    && PGVERSION=$(ls /usr/lib/postgresql | head -1) \
    && sudo -u postgres /usr/lib/postgresql/$PGVERSION/bin/initdb -D /var/lib/postgresql/data \
    && echo "host all all 127.0.0.1/32 scram-sha-256" >> /var/lib/postgresql/data/pg_hba.conf \
    && echo "listen_addresses = 'localhost'" >> /var/lib/postgresql/data/postgresql.conf

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Application
COPY . .

# Ensure Redis and Postgres can run (pg needs data dir)
RUN mkdir -p /var/run/postgresql && chown postgres:postgres /var/run/postgresql

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]



