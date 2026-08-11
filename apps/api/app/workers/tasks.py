import asyncio
import logging
from uuid import UUID

from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "stayprice",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
_eager = settings.CELERY_ALWAYS_EAGER or (
    settings.APP_ENV == "development" and "localhost" in settings.CELERY_BROKER_URL and not settings.is_production
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=_eager,
    task_eager_propagates=True,
    beat_schedule={
        "scrape-markets-daily": {
            "task": "app.workers.tasks.scrape_all_markets",
            "schedule": 60 * 60 * 24,
        },
    },
)


def sync_session() -> Session:
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    return Session(engine)


@celery_app.task(name="app.workers.tasks.scrape_all_markets")
def scrape_all_markets(prefer_live: bool = False) -> dict:
    from app.db.models import MarketListing, MarketSnapshot
    from app.modules.market.sources import REGIONS, get_market_source

    source = get_market_source(prefer_live=prefer_live)
    created = 0
    updated = 0
    with sync_session() as db:
        for region in REGIONS:
            listings = source.fetch_region(region["slug"])
            if not listings:
                listings = get_market_source(prefer_live=False).fetch_region(region["slug"])
            for raw in listings:
                existing = db.execute(
                    select(MarketListing).where(
                        MarketListing.external_listing_id == raw.external_id,
                        MarketListing.source == "airbnb",
                    )
                ).scalar_one_or_none()
                if existing:
                    existing.title = raw.title
                    existing.current_price = raw.price
                    existing.property_type = raw.property_type
                    existing.city = raw.city
                    existing.region = raw.region
                    existing.latitude = raw.latitude or region["lat"]
                    existing.longitude = raw.longitude or region["lng"]
                    existing.bedrooms = raw.bedrooms
                    existing.bathrooms = raw.bathrooms
                    existing.rating = raw.rating
                    existing.review_count = raw.review_count
                    existing.url = raw.url
                    existing.raw = raw.raw or {}
                    listing = existing
                    updated += 1
                else:
                    listing = MarketListing(
                        external_listing_id=raw.external_id,
                        source="airbnb",
                        title=raw.title,
                        url=raw.url,
                        property_type=raw.property_type,
                        city=raw.city,
                        region=raw.region,
                        latitude=raw.latitude or region["lat"],
                        longitude=raw.longitude or region["lng"],
                        bedrooms=raw.bedrooms,
                        bathrooms=raw.bathrooms,
                        rating=raw.rating,
                        review_count=raw.review_count,
                        current_price=raw.price,
                        raw=raw.raw or {},
                    )
                    db.add(listing)
                    db.flush()
                    created += 1
                db.add(
                    MarketSnapshot(
                        listing_id=listing.id,
                        price=raw.price,
                        rating=raw.rating,
                        review_count=raw.review_count,
                        meta={"region": region["slug"]},
                    )
                )
        db.commit()
    return {"created": created, "updated": updated}


async def _run_property_analysis_async(prediction_id: str, include_vision: bool = True) -> dict:
    from app.db.models import (
        CompSet,
        CompSetMember,
        Notification,
        Prediction,
        PredictionStatus,
        Property,
        PropertyAmenity,
        VisionAnalysis,
    )
    from app.ml.pricing import predict_price_band
    from app.modules.agents import agents
    from app.modules.market.comps import find_comps
    from app.modules.market.seasonality import get_seasonality_multiplier

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(
            select(Prediction)
            .options(
                selectinload(Prediction.property).selectinload(Property.photos),
                selectinload(Prediction.property)
                .selectinload(Property.amenities)
                .selectinload(PropertyAmenity.amenity),
            )
            .where(Prediction.id == UUID(prediction_id))
        )
        pred = result.scalar_one_or_none()
        if not pred:
            return {"error": "not_found"}
        prop = pred.property
        pred.status = PredictionStatus.running

        async def set_stage(stage: str, message: str, percent: int, **extra) -> None:
            traces = dict(pred.agent_traces or {})
            traces.update({"stage": stage, "stage_message": message, "percent": percent, **extra})
            pred.agent_traces = traces
            await db.commit()

        await set_stage("property_profile", "Profiling your property", 10)

        try:
            scrape_all_markets(prefer_live=False)

            property_data = {
                "id": str(prop.id),
                "title": prop.title,
                "property_type": prop.property_type.value,
                "city": prop.city,
                "state": prop.state,
                "country": prop.country,
                "neighborhood": prop.neighborhood,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "beds": prop.beds,
                "guests": prop.guests,
                "current_price": prop.current_price,
                "features": prop.features or {},
                "amenities": [pa.amenity.code for pa in prop.amenities if pa.amenity],
            }

            prop_brief = await agents.property_agent(property_data)
            await set_stage("market_comps", "Researching comparable listings", 25, property=prop_brief)

            comps_raw = await find_comps(db, prop, limit=25)
            comps_payload = [
                {
                    "title": c["listing"].title,
                    "price": c["listing"].current_price,
                    "bedrooms": c["listing"].bedrooms,
                    "bathrooms": c["listing"].bathrooms,
                    "type": c["listing"].property_type,
                    "rating": c["listing"].rating,
                    "similarity": c["score"],
                    "distance_km": c["distance_km"],
                }
                for c in comps_raw
            ]
            market_brief = await agents.market_agent(property_data, comps_payload)
            await set_stage("vision", "Analyzing listing photos", 45, market=market_brief)

            photo_urls = [p.url for p in prop.photos]
            if include_vision and photo_urls:
                vision = await agents.vision_agent(photo_urls)
            else:
                vision = {
                    "quality_score": 70,
                    "luxury_score": 65,
                    "cleanliness_score": 75,
                    "lighting_score": 70,
                    "furniture_score": 68,
                    "overall_score": 70,
                    "details": {},
                    "missing_amenities": [],
                    "suggestions": [],
                    "estimated_revenue_impact": 0,
                }

            await set_stage("pricing_model", "Running pricing model + seasonality", 65)

            prices = [c["listing"].current_price for c in comps_raw if c["listing"].current_price]
            prices_sorted = sorted(prices)
            comp_median = prices_sorted[len(prices_sorted) // 2] if prices_sorted else (prop.current_price or 200)
            comp_p75 = prices_sorted[int(len(prices_sorted) * 0.75)] if prices_sorted else comp_median * 1.15
            # Confidence boosts with denser comps
            comp_density = min(1.0, len(prices) / 20)

            features = {
                "city": prop.city,
                "property_type": prop.property_type.value,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "beds": prop.beds,
                "guests": prop.guests,
                "latitude": prop.latitude,
                "longitude": prop.longitude,
                "current_price": prop.current_price,
                "comp_median": comp_median,
                "comp_p75": comp_p75,
                "vision_overall": vision.get("overall_score", 70),
                "amenity_count": len(property_data["amenities"]),
            }
            band = predict_price_band(features)
            seasonality = await get_seasonality_multiplier(db, prop.city)
            pricing = await agents.pricing_agent(
                property_data,
                band["suggested_price"] * seasonality,
                band["min_price"] * seasonality,
                band["max_price"] * seasonality,
                market_brief,
                vision,
            )
            await set_stage("revenue", "Forecasting occupancy & revenue", 80)
            base_occ = 0.62 + min(0.15, len(prices) / 100)
            revenue = await agents.revenue_agent(pricing["suggested_price"], base_occ, seasonality)
            await set_stage("recommendations", "Generating improvement recommendations", 90)
            recs = await agents.recommendation_agent(property_data, vision, market_brief, pricing)

            confidence = min(0.95, float(band["confidence"]) * (0.7 + 0.3 * comp_density))
            pricing_method = (
                "hybrid_model_llm"
                if band["model_version"] and "heuristic" not in band["model_version"]
                else "comps_heuristic"
            )

            pred.suggested_price = pricing["suggested_price"]
            pred.min_price = pricing["min_price"]
            pred.max_price = pricing["max_price"]
            pred.expected_occupancy = revenue["expected_occupancy"]
            pred.monthly_revenue = revenue["monthly_revenue"]
            pred.annual_revenue = revenue["annual_revenue"]
            pred.confidence_score = round(confidence, 3)
            pred.model_version = band["model_version"]
            pred.features = features
            pred.strengths = recs.get("strengths") or []
            pred.weaknesses = recs.get("weaknesses") or []
            pred.recommendations = recs.get("recommendations") or []
            pred.explanation = pricing.get("explanation")
            pred.agent_traces = {
                "stage": "completed",
                "stage_message": "Analysis complete",
                "percent": 100,
                "property": prop_brief,
                "market": market_brief,
                "pricing": pricing,
                "revenue": revenue,
                "pricing_method": pricing_method,
                "comp_count": len(comps_raw),
                "seasonality_multiplier": seasonality,
            }
            pred.status = PredictionStatus.completed

            db.add(
                VisionAnalysis(
                    prediction_id=pred.id,
                    quality_score=vision.get("quality_score"),
                    luxury_score=vision.get("luxury_score"),
                    cleanliness_score=vision.get("cleanliness_score"),
                    lighting_score=vision.get("lighting_score"),
                    furniture_score=vision.get("furniture_score"),
                    overall_score=vision.get("overall_score"),
                    details=vision.get("details") or {},
                    missing_amenities=vision.get("missing_amenities") or [],
                    suggestions=vision.get("suggestions") or [],
                    estimated_revenue_impact=vision.get("estimated_revenue_impact"),
                )
            )

            cs = CompSet(property_id=prop.id, prediction_id=pred.id, summary={"count": len(comps_raw)})
            db.add(cs)
            await db.flush()
            for c in comps_raw:
                db.add(
                    CompSetMember(
                        comp_set_id=cs.id,
                        market_listing_id=c["listing"].id,
                        similarity_score=c["score"],
                        distance_km=c["distance_km"],
                    )
                )

            link = f"{settings.FRONTEND_URL}/app/properties/{prop.id}"
            db.add(
                Notification(
                    user_id=prop.user_id,
                    title="Analysis complete",
                    body=f"Price recommendation ready for {prop.title}: ${pricing['suggested_price']}/night",
                    type="prediction",
                    link=f"/app/properties/{prop.id}",
                )
            )
            await db.commit()

            # Best-effort email
            try:
                from app.db.models import User
                from app.modules.notifications.email import send_analysis_complete_email

                owner = await db.get(User, prop.user_id)
                if owner:
                    await send_analysis_complete_email(
                        owner.email, prop.title, float(pricing["suggested_price"]), link
                    )
            except Exception:
                logger.debug("analysis email skipped", exc_info=True)

            return {"status": "completed", "prediction_id": prediction_id}
        except Exception as exc:
            logger.exception("Analysis failed")
            pred.status = PredictionStatus.failed
            pred.error_message = str(exc)
            await db.commit()
            return {"status": "failed", "error": str(exc)}
        finally:
            await engine.dispose()


@celery_app.task(name="app.workers.tasks.run_property_analysis")
def run_property_analysis(prediction_id: str, include_vision: bool = True) -> dict:
    try:
        return asyncio.run(_run_property_analysis_async(prediction_id, include_vision))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run_property_analysis_async(prediction_id, include_vision))
        finally:
            loop.close()
