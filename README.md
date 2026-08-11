# StayPrice AI

AI Revenue Management Platform for Airbnb hosts.

Monorepo converting the legacy scrape → XGBoost → Streamlit prototype into a production-oriented SaaS:

- **Frontend:** Next.js 15 + TypeScript + Tailwind + React Query + Zustand
- **Backend:** FastAPI modular monolith + SQLAlchemy + Alembic + Celery
- **Database:** PostgreSQL 16
- **AI:** OpenRouter (LLM + Vision) with multi-agent orchestration
- **ML:** CatBoost pricing model
- **Billing:** Stripe (dev mode upgrades without keys)

## Structure

```
apps/api/          FastAPI backend
apps/web/          Next.js frontend
legacy/            Original prototype (preserved)
docker-compose.yml Postgres, Redis, MinIO, API, worker, beat, web
```

## One-command local start

```bash
./scripts/start.sh
```

Starts API (`:8000`) and Next.js (`:3000`) in one terminal. Stop with Ctrl+C. Logs: `scripts/.logs/`.

Requires Postgres/Redis running (e.g. `docker-compose up -d postgres redis`) and API venv + `npm install` already set up once.

## Quick start (Docker)

```bash
cp .env.example .env
docker-compose up --build
```

- Web: http://localhost:3000
- API docs: http://localhost:8000/v1/docs
- Postgres (host): `localhost:5436`
- Redis (host): `localhost:6382`
- MinIO console: http://localhost:9001

## Local development

### API

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Start Postgres + Redis (via compose or local)
export $(grep -v '^#' ../../.env | xargs)
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
celery -A app.workers.tasks.celery_app worker -l info
```

### Web

```bash
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Professional features (v1.1)

- Request IDs + JSON logs, optional Sentry
- Rate limiting, usage metering, plan entitlements
- Analysis progress stages + confidence labels in the UI
- Deep health checks (`/health/live`, `/health/ready`)
- Branded emails, improved PDF reports
- GitHub Actions CI + pytest (`apps/api/tests`)

See [docs/professionalization.md](docs/professionalization.md).

## Core flows

1. Register → verify email (token logged in API if Resend unset)
2. Create property via 6-step onboarding
3. Upload photos → complete onboarding
4. Run AI analysis → comps + vision + CatBoost + recommendations
5. Free plan capped at 5 properties; Billing upgrades to Pro

## Environment

See `.env.example` for `OPENROUTER_API_KEY`, Stripe, S3/MinIO, and database URLs.

## Legacy

The previous MySQL/Streamlit pipeline lives under `legacy/` for reference and is not used by the new stack.
