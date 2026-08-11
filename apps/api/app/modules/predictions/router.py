from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import write_audit
from app.core.deps import get_current_user, get_user_plan_tier
from app.core.entitlements import assert_can_analyze, entitlements_for, record_usage
from app.db.models import PlanTier, Prediction, PredictionStatus, Property, User
from app.db.session import get_db
from app.workers.tasks import run_property_analysis

router = APIRouter(tags=["predictions"])

ANALYSIS_STAGES = [
    "queued",
    "property_profile",
    "market_comps",
    "vision",
    "pricing_model",
    "revenue",
    "recommendations",
    "completed",
]


class PredictionOut(BaseModel):
    id: UUID
    property_id: UUID
    status: PredictionStatus
    suggested_price: float | None
    min_price: float | None
    max_price: float | None
    expected_occupancy: float | None
    monthly_revenue: float | None
    annual_revenue: float | None
    confidence_score: float | None
    confidence_label: str | None = None
    pricing_method: str | None = None
    model_version: str | None
    strengths: list
    weaknesses: list
    recommendations: list
    explanation: str | None
    error_message: str | None
    progress: dict | None = None
    vision: dict | None = None

    model_config = {"from_attributes": True}


def _confidence_label(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 0.75:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _progress_from_traces(traces: dict | None, status: PredictionStatus) -> dict:
    traces = traces or {}
    stage = traces.get("stage") or ("completed" if status == PredictionStatus.completed else "queued")
    try:
        idx = ANALYSIS_STAGES.index(stage) if stage in ANALYSIS_STAGES else 0
    except ValueError:
        idx = 0
    if status == PredictionStatus.failed:
        pct = traces.get("percent", 0)
    elif status == PredictionStatus.completed:
        pct = 100
    else:
        pct = int((idx / max(len(ANALYSIS_STAGES) - 1, 1)) * 100)
    return {
        "stage": stage,
        "percent": pct,
        "message": traces.get("stage_message") or stage.replace("_", " ").title(),
        "stages": ANALYSIS_STAGES,
    }


def _to_out(p: Prediction) -> PredictionOut:
    vision = None
    if p.vision_analysis:
        v = p.vision_analysis
        vision = {
            "quality_score": v.quality_score,
            "luxury_score": v.luxury_score,
            "cleanliness_score": v.cleanliness_score,
            "lighting_score": v.lighting_score,
            "furniture_score": v.furniture_score,
            "overall_score": v.overall_score,
            "details": v.details,
            "missing_amenities": v.missing_amenities,
            "suggestions": v.suggestions,
            "estimated_revenue_impact": v.estimated_revenue_impact,
        }
    traces = p.agent_traces or {}
    return PredictionOut(
        id=p.id,
        property_id=p.property_id,
        status=p.status,
        suggested_price=p.suggested_price,
        min_price=p.min_price,
        max_price=p.max_price,
        expected_occupancy=p.expected_occupancy,
        monthly_revenue=p.monthly_revenue,
        annual_revenue=p.annual_revenue,
        confidence_score=p.confidence_score,
        confidence_label=_confidence_label(p.confidence_score),
        pricing_method=traces.get("pricing_method") or ("model" if p.model_version and "heuristic" not in (p.model_version or "") else "comps_heuristic"),
        model_version=p.model_version,
        strengths=p.strengths or [],
        weaknesses=p.weaknesses or [],
        recommendations=p.recommendations or [],
        explanation=p.explanation,
        error_message=p.error_message,
        progress=_progress_from_traces(traces, p.status),
        vision=vision,
    )


@router.post("/properties/{property_id}/analyze", response_model=PredictionOut, status_code=202)
async def analyze_property(
    property_id: UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Property).options(selectinload(Property.photos)).where(Property.id == property_id, Property.user_id == user.id)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.onboarding_complete:
        raise HTTPException(status_code=400, detail="Complete onboarding before analysis")

    tier = get_user_plan_tier(user)
    await assert_can_analyze(db, user, tier)
    ents = entitlements_for(tier)
    include_vision = bool(ents["vision_full"] or len(prop.photos) <= ents["max_vision_photos"])

    prediction = Prediction(
        property_id=prop.id,
        status=PredictionStatus.pending,
        agent_traces={"stage": "queued", "stage_message": "Queued for analysis", "percent": 0},
    )
    db.add(prediction)
    await record_usage(db, user.id, "analysis", resource_type="prediction", resource_id=str(property_id))
    await write_audit(
        db,
        user_id=user.id,
        action="analysis.started",
        resource_type="property",
        resource_id=str(property_id),
        ip_address=request.client.host if request.client else None,
    )
    await db.flush()

    try:
        run_property_analysis.delay(str(prediction.id), include_vision=include_vision)
    except Exception:
        # Dev fallback only when broker unreachable
        run_property_analysis(str(prediction.id), include_vision=include_vision)
    return _to_out(prediction)


@router.get("/predictions/{prediction_id}", response_model=PredictionOut)
async def get_prediction(
    prediction_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.vision_analysis), selectinload(Prediction.property))
        .where(Prediction.id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if not pred or pred.property.user_id != user.id:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return _to_out(pred)


@router.get("/properties/{property_id}/predictions", response_model=list[PredictionOut])
async def list_predictions(
    property_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    prop = await db.get(Property, property_id)
    if not prop or prop.user_id != user.id:
        raise HTTPException(status_code=404, detail="Property not found")
    result = await db.execute(
        select(Prediction)
        .options(selectinload(Prediction.vision_analysis))
        .where(Prediction.property_id == property_id)
        .order_by(Prediction.created_at.desc())
    )
    return [_to_out(p) for p in result.scalars().all()]
