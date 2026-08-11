import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

router = APIRouter(tags=["health"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.get("/health/live")
async def live():
    return {"status": "alive", "version": settings.APP_VERSION}


@router.get("/health")
@router.get("/health/ready")
async def ready():
    checks: dict = {"api": True, "database": False, "redis": False}
    # Database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        logger.warning("health db check failed: %s", exc)

    # Redis
    try:
        import redis

        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        checks["redis"] = bool(r.ping())
    except Exception as exc:
        logger.warning("health redis check failed: %s", exc)

    ok = checks["database"]  # Redis optional for readiness in MVP; DB required
    status = "healthy" if ok else "degraded"
    code = 200 if ok else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=code,
        content={
            "status": status,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "checks": checks,
        },
    )
