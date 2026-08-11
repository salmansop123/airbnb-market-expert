import logging
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory fallback when Redis is down
_memory_buckets: dict[str, deque] = defaultdict(deque)


def _client_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return f"tok:{auth[7:24]}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    client = request.client.host if request.client else "unknown"
    return f"ip:{client}"


def _limit_for_path(path: str) -> tuple[int, int]:
    """Return (max_requests, window_seconds)."""
    if path.startswith("/v1/auth/login") or path.startswith("/v1/auth/register"):
        return settings.AUTH_RATE_LIMIT_PER_MINUTE, 60
    if "/analyze" in path:
        return settings.ANALYZE_RATE_LIMIT_PER_HOUR, 3600
    return settings.RATE_LIMIT_PER_MINUTE, 60


def _allow_memory(key: str, limit: int, window: int) -> bool:
    now = time.time()
    bucket = _memory_buckets[key]
    while bucket and bucket[0] <= now - window:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def _allow_redis(key: str, limit: int, window: int) -> bool | None:
    try:
        import redis

        r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        pipe = r.pipeline()
        now = time.time()
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        _, count, _, _ = pipe.execute()
        return int(count) < limit
    except Exception:
        logger.debug("rate_limit redis unavailable; using memory", exc_info=True)
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in {"/health", "/health/ready", "/health/live", "/"}:
            return await call_next(request)
        limit, window = _limit_for_path(request.url.path)
        key = f"rl:{_client_key(request)}:{request.url.path}:{window}"
        allowed = _allow_redis(key, limit, window)
        if allowed is None:
            allowed = _allow_memory(key, limit, window)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
        return await call_next(request)
