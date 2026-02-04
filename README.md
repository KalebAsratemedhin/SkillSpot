# SkillSpot

**SkillSpot** is a web app that connects people with trusted local professionals. Clients post jobs (e.g. plumbing, tutoring, gardening); professionals browse and apply; they agree on contracts, track work (fixed price or hourly), and handle payments—all in one place.

---

## What it does

- **Clients** post jobs with categories, location, and payment terms (fixed or hourly).
- **Professionals** browse jobs, apply, and receive invitations; they manage contracts and get paid via Stripe Connect.
- **Both** use real-time chat (WebSockets), in-app notifications, and structured contracts with milestones or time entries.
- **Payments** support fixed-price milestones and hourly time entries, with Stripe for payouts and optional Connect onboarding.

---

## Tech stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | Vue 3, TypeScript, Vite, Vue Router, Pinia, Tailwind CSS, Radix Vue, VeeValidate/Zod, Leaflet (maps), Axios |
| **Backend** | Django 5, Django REST Framework, Simple JWT, Daphne (ASGI), Celery, Django Channels |
| **Data** | PostgreSQL, Redis (cache + Channels + Celery broker) |
| **Payments** | Stripe, Stripe Connect |
| **API docs** | drf-spectacular (OpenAPI / Swagger / ReDoc) |

---

## Features

- **Auth** — Register, login, JWT refresh; role-aware (client vs professional).
- **Profiles** — User profiles, skills/tags, avatar upload.
- **Jobs** — Create, list, filter, detail; applications and invitations; map view.
- **Contracts** — Create from accepted job; fixed (milestones) or hourly; status workflow.
- **Payments** — Milestone payouts or time-entry based; Stripe Connect onboarding; payment history.
- **Messaging** — Real-time chat via WebSockets (Django Channels + Redis).
- **Notifications** — In-app notifications (e.g. new application, contract, payment); Celery for async sending.
- **Ratings** — Rate users after completed work.
- **API documentation** — Swagger UI at `/api/docs/`, ReDoc at `/api/redoc/`, schema at `/api/schema/`.

---

## Architecture

```
SkillSpot/
├── frontend/          # Vue 3 SPA (Vite)
│   ├── public/        # Static assets (e.g. favicon)
│   └── src/
│       ├── components/
│       ├── views/
│       ├── services/   # API clients
│       ├── stores/    # Pinia
│       └── router/
└── server/            # Django monolith
    ├── accounts/      # Auth
    ├── profiles/      # Users, skills, avatars
    ├── jobs/          # Jobs, applications, invitations
    ├── contracts/     # Contracts, milestones, time entries
    ├── payments/      # Payments, Stripe Connect
    ├── messaging/     # WebSocket chat (Channels)
    ├── notifications/ # Notifications + Celery tasks
    ├── ratings/
    ├── skillspot/     # Settings, ASGI, Celery, URLs
    ├── docker-compose.yml   # Postgres + Redis (local)
    ├── Dockerfile           # Single image (app + optional in-container Postgres/Redis)
    └── docker-entrypoint.sh
```

- **REST API** at `/api/v1/`; **WebSocket** for chat; **Daphne** serves HTTP and WS.
- **Celery** runs async tasks (e.g. notifications); **Redis** is broker and result backend, and used by Channels for ASGI.
- **Database**: PostgreSQL (or SQLite in dev if not configured). Use `DATABASE_URL` for an external DB, or in-container Postgres when running the single Docker image without `DATABASE_URL`.

---

## How to run

### Prerequisites

- Node.js (frontend), Python 3.10+ (backend), Docker (optional, for Postgres/Redis or full image).

### 1. Backend (local with Docker Postgres + Redis)

```bash
cd server
cp .env.example .env   # Edit with SECRET_KEY, etc.
python3 -m venv venv
source venv/bin/activate   # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
./start.sh
```

`start.sh` starts Docker Compose (Postgres + Redis), waits for them, runs Celery in the background, then starts Daphne on `http://127.0.0.1:8000`.

### 2. Backend (local without Docker — SQLite, no Redis/Celery/Channels)

Set in `server/.env` so that Postgres/Redis are not required (e.g. no `POSTGRES_*` / `DB_HOST`; Django can fall back to SQLite). Run migrations and Daphne manually:

```bash
cd server
source venv/bin/activate
python3 manage.py migrate
daphne -b 127.0.0.1 -p 8000 skillspot.asgi:application
```

### 3. Backend (single Docker image)

Build and run the image that includes the app plus in-container Postgres and Redis (or set `DATABASE_URL` to use an external DB):

```bash
cd server
docker build -t skillspot .
docker run -p 8000:8000 -e SECRET_KEY=your-secret skillspot
```

Optional: pass `ALLOWED_HOSTS`, `DATABASE_URL`, etc., as env vars.

### 4. Frontend

```bash
cd frontend
cp .env.example .env   # Set VITE_API_BASE_URL to backend (e.g. http://localhost:8000)
npm install
npm run dev
```

Open the URL shown (e.g. `http://localhost:5173`). The browser tab will show the SkillSpot favicon.

### 5. Production / deploy

- **Backend**: Deploy the Docker image (e.g. to Render) or run Django with Gunicorn/Daphne behind a reverse proxy; set `ALLOWED_HOSTS`, `DATABASE_URL`, `SECRET_KEY`, CORS, and Stripe env vars.
- **Frontend**: `npm run build` and serve the `dist/` folder (or deploy to a static host) with `VITE_API_BASE_URL` pointing to the backend.
- **Persistent data and admin**: If the app uses in-container Postgres, the database is wiped on each deploy. For a persistent DB (and to keep your admin user), add a **PostgreSQL** service (e.g. Render Postgres), set **`DATABASE_URL`** in the backend’s environment, and redeploy. To (re)create an admin user on startup, set **`DJANGO_SUPERUSER_USERNAME`**, **`DJANGO_SUPERUSER_PASSWORD`**, and optionally **`DJANGO_SUPERUSER_EMAIL`**; the entrypoint runs `createsuperuser --noinput` when these are set (idempotent if the user already exists).

---

## Quick reference

| Action | Command |
|--------|--------|
| Backend (full stack local) | `cd server && ./start.sh` |
| Backend (Docker single container) | `cd server && docker build -t skillspot . && docker run -p 8000:8000 -e SECRET_KEY=xxx skillspot` |
| Frontend dev | `cd frontend && npm run dev` |
| API docs (after backend running) | `http://localhost:8000/api/docs/` (Swagger), `http://localhost:8000/api/redoc/` (ReDoc) |



