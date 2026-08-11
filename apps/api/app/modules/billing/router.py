from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.models import Plan, PlanTier, Subscription, SubscriptionStatus, User
from app.db.session import get_db

router = APIRouter(prefix="/billing", tags=["billing"])
settings = get_settings()
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutResponse(BaseModel):
    checkout_url: str | None
    message: str


class PortalResponse(BaseModel):
    portal_url: str


class PlanOut(BaseModel):
    code: str
    name: str
    description: str | None
    property_limit: int | None
    price_monthly_cents: int
    features: dict


@router.get("/plans", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).order_by(Plan.price_monthly_cents))
    return [
        PlanOut(
            code=p.code.value,
            name=p.name,
            description=p.description,
            property_limit=p.property_limit,
            price_monthly_cents=p.price_monthly_cents,
            features=p.features or {},
        )
        for p in result.scalars().all()
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    plan: str = Query("pro"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tier = PlanTier.pro if plan == "pro" else PlanTier.business
    result = await db.execute(select(Plan).where(Plan.code == tier))
    plan_row = result.scalar_one_or_none()
    if not plan_row:
        raise HTTPException(status_code=404, detail="Plan not found")

    if not settings.STRIPE_SECRET_KEY:
        # Dev bypass: upgrade locally
        sub_result = await db.execute(
            select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.user_id == user.id)
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            sub.plan_id = plan_row.id
            sub.status = SubscriptionStatus.active
        else:
            db.add(Subscription(user_id=user.id, plan_id=plan_row.id, status=SubscriptionStatus.active))
        return CheckoutResponse(checkout_url=None, message=f"Dev mode: upgraded to {tier.value}")

    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.full_name or user.email)
        user.stripe_customer_id = customer["id"]
        await db.flush()

    price_id = plan_row.stripe_price_id or (
        settings.STRIPE_PRO_PRICE_ID if tier == PlanTier.pro else settings.STRIPE_BUSINESS_PRICE_ID
    )
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe price not configured")

    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/app/billing?success=1",
        cancel_url=f"{settings.FRONTEND_URL}/app/billing?canceled=1",
        metadata={"user_id": str(user.id), "plan": tier.value},
    )
    return CheckoutResponse(checkout_url=session.url, message="Checkout session created")


@router.post("/portal", response_model=PortalResponse)
async def billing_portal(user: User = Depends(get_current_user)):
    if not settings.STRIPE_SECRET_KEY or not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Stripe not configured or no customer")
    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/app/billing",
    )
    return PortalResponse(portal_url=session.url)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        import json

        event = json.loads(payload)

    etype = event["type"] if isinstance(event, dict) else event.type
    data = event["data"]["object"] if isinstance(event, dict) else event.data.object

    if etype == "checkout.session.completed":
        user_id = (data.get("metadata") or {}).get("user_id")
        plan_code = (data.get("metadata") or {}).get("plan", "pro")
        if user_id:
            plan = (
                await db.execute(select(Plan).where(Plan.code == PlanTier(plan_code)))
            ).scalar_one_or_none()
            user = await db.get(User, UUID(user_id))
            if user and plan:
                sub = (
                    await db.execute(select(Subscription).where(Subscription.user_id == user.id))
                ).scalar_one_or_none()
                if sub:
                    sub.plan_id = plan.id
                    sub.status = SubscriptionStatus.active
                    sub.stripe_subscription_id = data.get("subscription")
                else:
                    db.add(
                        Subscription(
                            user_id=user.id,
                            plan_id=plan.id,
                            status=SubscriptionStatus.active,
                            stripe_subscription_id=data.get("subscription"),
                        )
                    )
    return {"received": True}


class UsageSummary(BaseModel):
    plan: str
    analyses_this_month: int
    chat_today: int
    entitlements: dict


@router.get("/usage", response_model=UsageSummary)
async def usage_summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.core.deps import get_user_plan_tier
    from app.core.entitlements import count_usage, day_start, entitlements_for, month_start

    tier = get_user_plan_tier(user)
    return UsageSummary(
        plan=tier.value,
        analyses_this_month=await count_usage(db, user.id, "analysis", month_start()),
        chat_today=await count_usage(db, user.id, "chat", day_start()),
        entitlements=entitlements_for(tier),
    )
