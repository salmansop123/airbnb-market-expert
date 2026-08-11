from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.db.models import (
    EmailVerificationToken,
    PasswordResetToken,
    Plan,
    PlanTier,
    RefreshToken,
    Subscription,
    SubscriptionStatus,
    User,
    UserSettings,
)
from app.db.session import get_db
from app.modules.notifications.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    is_verified: bool
    role: str
    plan: str

    model_config = {"from_attributes": True}


async def _ensure_free_subscription(db: AsyncSession, user: User) -> None:
    result = await db.execute(select(Plan).where(Plan.code == PlanTier.free))
    plan = result.scalar_one_or_none()
    if not plan:
        plan = Plan(
            code=PlanTier.free,
            name="Free",
            description="Up to 5 properties, basic AI",
            property_limit=5,
            price_monthly_cents=0,
            features={"vision": False, "reports": False, "chat": True},
        )
        db.add(plan)
        await db.flush()
    sub = Subscription(user_id=user.id, plan_id=plan.id, status=SubscriptionStatus.active)
    db.add(sub)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    db.add(UserSettings(user_id=user.id))
    await _ensure_free_subscription(db, user)

    token = token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )
    )
    await send_verification_email(user.email, token)
    return MessageResponse(message="Registered. Please verify your email.")


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access = create_access_token(str(user.id), {"role": user.role.value})
    refresh, jti, expires = create_refresh_token(str(user.id))
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = safe_decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    jti = payload.get("jti")
    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
    stored = result.scalar_one_or_none()
    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    stored.revoked = True
    user_id = payload["sub"]
    access = create_access_token(user_id)
    new_refresh, new_jti, expires = create_refresh_token(user_id)
    db.add(RefreshToken(user_id=UUID(user_id), jti=new_jti, expires_at=expires))
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    payload = safe_decode_token(body.refresh_token)
    if payload and payload.get("jti"):
        result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload["jti"]))
        stored = result.scalar_one_or_none()
        if stored and stored.user_id == user.id:
            stored.revoked = True
    return MessageResponse(message="Logged out")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailVerificationToken).where(EmailVerificationToken.token == body.token))
    row = result.scalar_one_or_none()
    if not row or row.used or row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user = await db.get(User, row.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    row.used = True
    return MessageResponse(message="Email verified")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    # Always return success to avoid email enumeration
    if user:
        token = token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
            )
        )
        await send_password_reset_email(user.email, token)
    return MessageResponse(message="If that email exists, a reset link was sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == body.token))
    row = result.scalar_one_or_none()
    if not row or row.used or row.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = await db.get(User, row.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(body.new_password)
    row.used = True
    return MessageResponse(message="Password updated")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(selectinload(User.subscription).selectinload(Subscription.plan))
        .where(User.id == user.id)
    )
    u = result.scalar_one()
    plan = u.subscription.plan.code.value if u.subscription and u.subscription.plan else "free"
    return UserOut(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        is_verified=u.is_verified,
        role=u.role.value,
        plan=plan,
    )
