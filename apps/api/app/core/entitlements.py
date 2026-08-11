"""Plan entitlements and monthly usage metering."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import PlanTier, UsageEvent, User

settings = get_settings()


PLAN_FEATURES = {
    PlanTier.free: {
        "vision_full": False,
        "reports": False,
        "chat": True,
        "api_access": False,
        "max_vision_photos": settings.FREE_VISION_PHOTOS,
        "analyses_per_month": settings.FREE_ANALYSES_PER_MONTH,
        "chat_per_day": settings.FREE_CHAT_PER_DAY,
        "property_limit": settings.FREE_PROPERTY_LIMIT,
    },
    PlanTier.pro: {
        "vision_full": True,
        "reports": True,
        "chat": True,
        "api_access": False,
        "max_vision_photos": 30,
        "analyses_per_month": settings.PRO_ANALYSES_PER_MONTH,
        "chat_per_day": 500,
        "property_limit": None,
    },
    PlanTier.business: {
        "vision_full": True,
        "reports": True,
        "chat": True,
        "api_access": True,
        "max_vision_photos": 30,
        "analyses_per_month": settings.BUSINESS_ANALYSES_PER_MONTH,
        "chat_per_day": 5000,
        "property_limit": None,
    },
}


def entitlements_for(tier: PlanTier) -> dict:
    return dict(PLAN_FEATURES.get(tier, PLAN_FEATURES[PlanTier.free]))


def month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def day_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


# Back-compat aliases
_month_start = month_start
_day_start = day_start


async def count_usage(db: AsyncSession, user_id: UUID, event_type: str, since: datetime) -> int:
    result = await db.scalar(
        select(func.count())
        .select_from(UsageEvent)
        .where(
            UsageEvent.user_id == user_id,
            UsageEvent.event_type == event_type,
            UsageEvent.created_at >= since,
        )
    )
    return int(result or 0)


async def record_usage(
    db: AsyncSession,
    user_id: UUID,
    event_type: str,
    *,
    resource_type: str | None = None,
    resource_id: str | None = None,
    meta: dict | None = None,
) -> None:
    db.add(
        UsageEvent(
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            meta=meta or {},
        )
    )


async def assert_can_analyze(db: AsyncSession, user: User, tier: PlanTier) -> None:
    ents = entitlements_for(tier)
    used = await count_usage(db, user.id, "analysis", _month_start())
    limit = ents["analyses_per_month"]
    if limit is not None and used >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Monthly analysis limit ({limit}) reached for {tier.value} plan. Upgrade to continue.",
        )


async def assert_can_chat(db: AsyncSession, user: User, tier: PlanTier) -> None:
    ents = entitlements_for(tier)
    if not ents["chat"]:
        raise HTTPException(status_code=402, detail="Chat not available on your plan.")
    used = await count_usage(db, user.id, "chat", _day_start())
    limit = ents["chat_per_day"]
    if used >= limit:
        raise HTTPException(status_code=429, detail="Daily chat limit reached.")


async def assert_can_report(tier: PlanTier) -> None:
    if not entitlements_for(tier)["reports"]:
        raise HTTPException(status_code=402, detail="PDF reports require Pro or Business.")
