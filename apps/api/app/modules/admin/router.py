from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_user_plan_tier, require_admin
from app.core.entitlements import count_usage, entitlements_for, month_start
from app.db.models import ModelRegistry, User
from app.db.session import get_db
from app.ml.pricing import artifacts_dir, seed_and_train

router = APIRouter(prefix="/admin", tags=["admin"])


class ModelOut(BaseModel):
    id: UUID
    name: str
    version: str
    algorithm: str
    artifact_path: str
    metrics: dict
    is_active: bool

    model_config = {"from_attributes": True}


class UsageOut(BaseModel):
    analyses_this_month: int
    plan: str
    entitlements: dict


@router.get("/models", response_model=list[ModelOut])
async def list_models(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ModelRegistry).order_by(ModelRegistry.created_at.desc()))
    return [ModelOut.model_validate(m) for m in result.scalars().all()]


@router.post("/models/retrain", response_model=ModelOut)
async def retrain_model(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    meta = seed_and_train()
    await db.execute(update(ModelRegistry).values(is_active=False))
    row = ModelRegistry(
        name="price_catboost",
        version=meta["version"],
        algorithm="catboost",
        artifact_path=meta["path"],
        metrics={"mae": meta.get("mae"), "n_rows": meta.get("n_rows")},
        is_active=True,
        feature_schema={"features": ["city", "property_type", "bedrooms", "comp_median", "vision_overall"]},
    )
    db.add(row)
    await db.flush()
    return ModelOut.model_validate(row)


@router.get("/usage/me", response_model=UsageOut)
async def my_usage(user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    tier = get_user_plan_tier(user)
    used = await count_usage(db, user.id, "analysis", month_start())
    return UsageOut(analyses_this_month=used, plan=tier.value, entitlements=entitlements_for(tier))


@router.get("/artifacts")
async def artifacts_info(admin: User = Depends(require_admin)):
    path = artifacts_dir()
    files = [p.name for p in path.glob("*")] if path.exists() else []
    return {"dir": str(path), "files": files}
