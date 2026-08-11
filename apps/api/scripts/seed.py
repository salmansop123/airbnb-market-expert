"""Seed plans, amenities, holidays, seasonality, market data, and ML model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Amenity, HolidayCalendar, Plan, PlanTier, SeasonalityIndex
from app.ml.pricing import seed_and_train
from app.workers.tasks import scrape_all_markets

AMENITIES = [
    ("wifi", "Wifi", "essentials"),
    ("kitchen", "Kitchen", "essentials"),
    ("washer", "Washer", "essentials"),
    ("dryer", "Dryer", "essentials"),
    ("air_conditioning", "Air conditioning", "climate"),
    ("heating", "Heating", "climate"),
    ("tv", "TV", "entertainment"),
    ("workspace", "Dedicated workspace", "work"),
    ("parking", "Free parking", "parking"),
    ("ev_charger", "EV charger", "parking"),
    ("pool", "Pool", "outdoor"),
    ("hot_tub", "Hot tub", "outdoor"),
    ("patio", "Patio", "outdoor"),
    ("bbq", "BBQ grill", "outdoor"),
    ("garden", "Garden", "outdoor"),
    ("balcony", "Balcony", "outdoor"),
    ("elevator", "Elevator", "accessibility"),
    ("wheelchair", "Wheelchair accessible", "accessibility"),
    ("pet_friendly", "Pet friendly", "rules"),
    ("smoking_allowed", "Smoking allowed", "rules"),
    ("self_checkin", "Self check-in", "access"),
    ("security_cameras", "Security cameras", "safety"),
    ("smoke_alarm", "Smoke alarm", "safety"),
    ("carbon_monoxide_alarm", "Carbon monoxide alarm", "safety"),
    ("fire_extinguisher", "Fire extinguisher", "safety"),
    ("first_aid", "First aid kit", "safety"),
    ("hair_dryer", "Hair dryer", "bathroom"),
    ("shampoo", "Shampoo", "bathroom"),
    ("hot_water", "Hot water", "bathroom"),
    ("coffee_maker", "Coffee maker", "kitchen"),
    ("dishwasher", "Dishwasher", "kitchen"),
    ("microwave", "Microwave", "kitchen"),
    ("refrigerator", "Refrigerator", "kitchen"),
    ("oven", "Oven", "kitchen"),
    ("stove", "Stove", "kitchen"),
    ("gym", "Gym", "facilities"),
    ("beach_access", "Beach access", "location"),
    ("lake_access", "Lake access", "location"),
    ("mountain_view", "Mountain view", "views"),
    ("ocean_view", "Ocean view", "views"),
    ("city_view", "City skyline view", "views"),
    ("crib", "Crib", "family"),
    ("high_chair", "High chair", "family"),
]


def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL_SYNC)
    with Session(engine) as db:
        # Plans
        plans = [
            (PlanTier.free, "Free", "Up to 5 properties, basic AI", 5, 0, {"vision": "limited", "reports": False}),
            (PlanTier.pro, "Pro", "Unlimited properties, Vision AI, reports", None, 2999, {"vision": True, "reports": True}),
            (
                PlanTier.business,
                "Business",
                "Portfolio, API access, multi-user",
                None,
                9999,
                {"vision": True, "reports": True, "api": True, "seats": True},
            ),
        ]
        for code, name, desc, limit, price, features in plans:
            existing = db.execute(select(Plan).where(Plan.code == code)).scalar_one_or_none()
            if not existing:
                db.add(
                    Plan(
                        id=uuid.uuid4(),
                        code=code,
                        name=name,
                        description=desc,
                        property_limit=limit,
                        price_monthly_cents=price,
                        features=features,
                    )
                )

        for code, name, category in AMENITIES:
            existing = db.execute(select(Amenity).where(Amenity.code == code)).scalar_one_or_none()
            if not existing:
                db.add(Amenity(id=uuid.uuid4(), code=code, name=name, category=category))

        # US holidays sample
        year = datetime.now(timezone.utc).year
        holidays = [
            ("US", "New Year's Day", datetime(year, 1, 1, tzinfo=timezone.utc), 1.25),
            ("US", "Independence Day", datetime(year, 7, 4, tzinfo=timezone.utc), 1.3),
            ("US", "Thanksgiving", datetime(year, 11, 26, tzinfo=timezone.utc), 1.2),
            ("US", "Christmas", datetime(year, 12, 25, tzinfo=timezone.utc), 1.35),
        ]
        for country, name, date, mult in holidays:
            db.add(HolidayCalendar(id=uuid.uuid4(), country=country, name=name, date=date, multiplier=mult))

        cities = ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"]
        for city in cities:
            for month in range(1, 13):
                for dow in range(7):
                    # Summer boost, weekend boost
                    mult = 1.0
                    if month in (6, 7, 8):
                        mult *= 1.12
                    if month in (12, 1):
                        mult *= 1.08
                    if dow >= 5:
                        mult *= 1.1
                    existing = db.execute(
                        select(SeasonalityIndex).where(
                            SeasonalityIndex.city == city,
                            SeasonalityIndex.month == month,
                            SeasonalityIndex.day_of_week == dow,
                        )
                    ).scalar_one_or_none()
                    if not existing:
                        db.add(
                            SeasonalityIndex(
                                id=uuid.uuid4(),
                                city=city,
                                month=month,
                                day_of_week=dow,
                                multiplier=round(mult, 3),
                            )
                        )
        db.commit()

    print("Seeding market listings...")
    print(scrape_all_markets(prefer_live=False))
    print("Training CatBoost seed model...")
    print(seed_and_train())
    print("Seed complete.")


if __name__ == "__main__":
    seed()
