# Professionalization notes

Implemented upgrades toward production SaaS quality:

## Ops
- JSON structured logging + `X-Request-ID`
- Optional Sentry (`SENTRY_DSN`)
- Deep health: `/health/live`, `/health` / `/health/ready` (DB + Redis checks)
- Celery eager flag via `CELERY_ALWAYS_EAGER`

## Security
- Redis-backed rate limiting (memory fallback)
- Hardened CORS methods/headers
- Audit log writes on analysis start
- Plan entitlements + monthly/daily usage metering (`usage_events`)

## Product
- Analysis progress stages in `agent_traces` (polled by UI)
- Confidence label + pricing method transparency
- Branded email templates (Resend)
- Professional PDF HTML layout for reports
- Dashboard empty/loading states + usage meters

## ML / admin
- Admin model registry list/retrain (`/v1/admin/*`)
- Seasonality applied in pricing pipeline
- Comp-density adjusted confidence

## Engineering
- pytest unit tests
- GitHub Actions CI (API tests + web typecheck)
- `scripts/export-openapi.sh` for OpenAPI export

## Still recommended next
- Playwright e2e
- Staging deploy pipeline
- Paid market data source
- WebSockets for live progress
- Org/multi-user Business seats
