import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketListing, Property


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _similarity(prop: Property, listing: MarketListing, distance_km: float | None) -> float:
    score = 0.0
    if listing.property_type and prop.property_type:
        if listing.property_type.lower().replace(" ", "_") == prop.property_type.value:
            score += 0.35
        elif prop.property_type.value in (listing.property_type or "").lower():
            score += 0.2
    if prop.bedrooms is not None and listing.bedrooms is not None:
        diff = abs(prop.bedrooms - listing.bedrooms)
        score += max(0, 0.25 - diff * 0.1)
    if prop.bathrooms is not None and listing.bathrooms is not None:
        diff = abs(prop.bathrooms - listing.bathrooms)
        score += max(0, 0.15 - diff * 0.05)
    if prop.guests is not None and listing.guests is not None:
        diff = abs(prop.guests - listing.guests)
        score += max(0, 0.1 - diff * 0.02)
    if distance_km is not None:
        if distance_km <= 2:
            score += 0.15
        elif distance_km <= 5:
            score += 0.1
        elif distance_km <= 10:
            score += 0.05
    elif prop.city and listing.city and prop.city.lower() == listing.city.lower():
        score += 0.1
    return round(min(score, 1.0), 4)


async def find_comps(db: AsyncSession, prop: Property, limit: int = 20) -> list[dict[str, Any]]:
    q = select(MarketListing).where(MarketListing.current_price.is_not(None))
    if prop.city:
        q = q.where(MarketListing.city.ilike(prop.city))
    if prop.bedrooms is not None:
        q = q.where(MarketListing.bedrooms.between(max(0, prop.bedrooms - 1), prop.bedrooms + 1))
    result = await db.execute(q.limit(200))
    candidates = list(result.scalars().all())

    # Expand if too few
    if len(candidates) < 10 and prop.city:
        result = await db.execute(
            select(MarketListing).where(MarketListing.current_price.is_not(None)).limit(200)
        )
        candidates = list(result.scalars().all())

    scored = []
    for listing in candidates:
        dist = None
        if prop.latitude and prop.longitude and listing.latitude and listing.longitude:
            dist = haversine_km(prop.latitude, prop.longitude, listing.latitude, listing.longitude)
            if dist > 25:
                continue
        score = _similarity(prop, listing, dist)
        scored.append({"listing": listing, "score": score, "distance_km": round(dist, 2) if dist else None})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
