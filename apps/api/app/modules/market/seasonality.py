from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HolidayCalendar, SeasonalityIndex


async def get_seasonality_multiplier(db: AsyncSession, city: str | None, when: datetime | None = None) -> float:
    when = when or datetime.utcnow()
    mult = 1.0
    if city:
        result = await db.execute(
            select(SeasonalityIndex).where(
                SeasonalityIndex.city.ilike(city),
                SeasonalityIndex.month == when.month,
                SeasonalityIndex.day_of_week == when.weekday(),
            )
        )
        row = result.scalar_one_or_none()
        if row:
            mult *= row.multiplier
    # Holiday boost (US default)
    start = when.replace(hour=0, minute=0, second=0, microsecond=0)
    end = when.replace(hour=23, minute=59, second=59)
    result = await db.execute(
        select(HolidayCalendar).where(
            and_(HolidayCalendar.date >= start, HolidayCalendar.date <= end)
        )
    )
    holiday = result.scalar_one_or_none()
    if holiday:
        mult *= holiday.multiplier
    # Weekend uplift fallback
    if when.weekday() >= 5:
        mult *= 1.08
    return round(mult, 4)
