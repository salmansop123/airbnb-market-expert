import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.models import MarketListing, Property, User
from app.db.session import get_db
from app.modules.market.comps import find_comps, haversine_km

router = APIRouter(prefix="/market", tags=["market"])


class CompOut(BaseModel):
    id: UUID
    title: str | None
    city: str | None
    property_type: str | None
    bedrooms: int | None
    bathrooms: float | None
    current_price: float | None
    rating: float | None
    review_count: int | None
    similarity_score: float
    distance_km: float | None
    url: str | None


class TrendOut(BaseModel):
    city: str
    listing_count: int
    avg_price: float | None
    median_price: float | None
    min_price: float | None
    max_price: float | None


@router.get("/comps", response_model=list[CompOut])
async def get_comps(
    property_id: UUID = Query(...),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await db.get(Property, property_id)
    if not prop or prop.user_id != user.id:
        raise HTTPException(status_code=404, detail="Property not found")
    comps = await find_comps(db, prop, limit=limit)
    return [
        CompOut(
            id=c["listing"].id,
            title=c["listing"].title,
            city=c["listing"].city,
            property_type=c["listing"].property_type,
            bedrooms=c["listing"].bedrooms,
            bathrooms=c["listing"].bathrooms,
            current_price=c["listing"].current_price,
            rating=c["listing"].rating,
            review_count=c["listing"].review_count,
            similarity_score=c["score"],
            distance_km=c["distance_km"],
            url=c["listing"].url,
        )
        for c in comps
    ]


@router.get("/trends", response_model=list[TrendOut])
async def market_trends(
    city: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(MarketListing)
    if city:
        q = q.where(MarketListing.city.ilike(city))
    result = await db.execute(q)
    listings = result.scalars().all()
    by_city: dict[str, list[float]] = {}
    for listing in listings:
        c = listing.city or "Unknown"
        if listing.current_price is not None:
            by_city.setdefault(c, []).append(listing.current_price)
    out = []
    for c, prices in sorted(by_city.items()):
        prices_sorted = sorted(prices)
        mid = len(prices_sorted) // 2
        median = prices_sorted[mid] if prices_sorted else None
        if prices_sorted and len(prices_sorted) % 2 == 0 and mid > 0:
            median = (prices_sorted[mid - 1] + prices_sorted[mid]) / 2
        out.append(
            TrendOut(
                city=c,
                listing_count=len(prices),
                avg_price=round(sum(prices) / len(prices), 2) if prices else None,
                median_price=round(median, 2) if median else None,
                min_price=min(prices) if prices else None,
                max_price=max(prices) if prices else None,
            )
        )
    return out
