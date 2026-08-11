from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import init_sentry, setup_logging
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.modules.admin.health import router as health_router
from app.modules.admin.router import router as admin_router
from app.modules.agents.router import router as chat_router
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.market.router import router as market_router
from app.modules.notifications.router import router as notifications_router
from app.modules.predictions.router import router as predictions_router
from app.modules.properties.router import router as properties_router
from app.modules.reports.router import router as reports_router

settings = get_settings()
setup_logging()
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.ml.pricing import artifacts_dir, seed_and_train

        if not (artifacts_dir() / "active_model.pkl").exists():
            seed_and_train()
    except Exception:
        pass
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Middleware order: last added runs first
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Idempotency-Key"],
    expose_headers=["X-Request-ID"],
)

prefix = settings.API_V1_PREFIX
app.include_router(health_router)
app.include_router(auth_router, prefix=prefix)
app.include_router(properties_router, prefix=prefix)
app.include_router(predictions_router, prefix=prefix)
app.include_router(market_router, prefix=prefix)
app.include_router(billing_router, prefix=prefix)
app.include_router(reports_router, prefix=prefix)
app.include_router(chat_router, prefix=prefix)
app.include_router(notifications_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "ok",
        "docs": f"{prefix}/docs",
    }
