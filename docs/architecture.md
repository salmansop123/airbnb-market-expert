# StayPrice AI — Architecture notes

See the implementation blueprint in the project plan. Summary:

- Modular monolith FastAPI under `apps/api`
- Next.js App Router under `apps/web`
- PostgreSQL schema via Alembic `0001_initial`
- Celery workers for scrape + analysis
- OpenRouter agents (mockable without API key)
- CatBoost pricing with hybrid LLM adjustment
- Legacy prototype preserved in `legacy/`
