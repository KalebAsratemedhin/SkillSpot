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
└── backend/           # Django monolith
    ├── accounts/ profiles/ jobs/ contracts/ payments/
    ├── messaging/ notifications/ ratings/
    ├── skillspot/           # Settings, ASGI, Celery, URLs, runapp command
    ├── docker-compose.yml   # Local: Postgres + Redis + app
    └── Dockerfile           # App image; CMD = manage.py runapp
```

- **REST API** at `/api/v1/`; **WebSocket** for chat; **Daphne** serves HTTP and WS.
- **Boot**: `python manage.py runapp` migrates, starts Celery, then Daphne. Static files are collected at **image build** time (Whitenoise).
- **Postgres / Redis** are external. Locally they come from Compose; in production use hosted Postgres + Upstash (or similar).

---

## How to run

### Prerequisites

- Node.js (frontend), Docker (backend).

### 1. Backend (Docker Compose)

```bash
cd backend
cp .env.example .env   # Edit SECRET_KEY, Stripe keys, etc.
docker compose up --build
```

That starts Postgres, Redis, and the app on `http://localhost:8000`.

Useful commands:

```bash
docker compose up --build -d   # detached
docker compose logs -f web     # app logs
docker compose down            # stop
```

### 2. Backend (production image)

Same Dockerfile; point at external services (no Compose DB/Redis):

```bash
cd backend
docker build -t skillspot .
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret \
  -e DATABASE_URL=postgres://... \
  -e REDIS_URL=rediss://default:TOKEN@HOST.upstash.io:6379 \
  skillspot
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev
```

### 4. Production / deploy

- Deploy the **app image** with `DATABASE_URL`, `REDIS_URL` (Upstash TLS), `SECRET_KEY`, `ALLOWED_HOSTS`, Stripe vars.
- Container `CMD` is `python manage.py runapp` (migrate → Celery → Daphne).
- Optional first-boot admin: `DJANGO_SUPERUSER_EMAIL` + `DJANGO_SUPERUSER_PASSWORD`.
- Upstash: Fixed plan is safer if Celery traffic grows; result backend is off by default.

---

## Quick reference

| Action | Command |
|--------|--------|
| Backend local | `cd backend && docker compose up --build` |
| Backend prod image | `cd backend && docker build -t skillspot . && docker run ...` |
| Frontend dev | `cd frontend && npm run dev` |
| API docs | `http://localhost:8000/api/docs/` |



