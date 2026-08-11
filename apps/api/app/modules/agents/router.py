from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_user_plan_tier
from app.core.entitlements import assert_can_chat, record_usage
from app.db.models import AIConversation, Message, Prediction, Property, User
from app.db.session import get_db
from app.modules.agents import agents

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class MessageOut(BaseModel):
    id: UUID
    role: str
    content: str

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: UUID
    messages: list[MessageOut]


@router.post("/properties/{property_id}/chat", response_model=ChatResponse)
async def chat(
    property_id: UUID,
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await db.get(Property, property_id)
    if not prop or prop.user_id != user.id:
        raise HTTPException(status_code=404, detail="Property not found")

    tier = get_user_plan_tier(user)
    await assert_can_chat(db, user, tier)

    if body.conversation_id:
        result = await db.execute(
            select(AIConversation)
            .options(selectinload(AIConversation.messages))
            .where(AIConversation.id == body.conversation_id, AIConversation.user_id == user.id)
        )
        convo = result.scalar_one_or_none()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        convo = AIConversation(property_id=prop.id, user_id=user.id, title=body.message[:80])
        db.add(convo)
        await db.flush()

    db.add(Message(conversation_id=convo.id, role="user", content=body.message))

    pred_result = await db.execute(
        select(Prediction)
        .where(Prediction.property_id == prop.id)
        .order_by(Prediction.created_at.desc())
        .limit(1)
    )
    pred = pred_result.scalar_one_or_none()
    context = {
        "property": {
            "title": prop.title,
            "city": prop.city,
            "type": prop.property_type.value,
            "bedrooms": prop.bedrooms,
            "current_price": prop.current_price,
        },
        "latest_prediction": None,
    }
    if pred:
        context["latest_prediction"] = {
            "suggested_price": pred.suggested_price,
            "min_price": pred.min_price,
            "max_price": pred.max_price,
            "monthly_revenue": pred.monthly_revenue,
            "recommendations": pred.recommendations,
            "explanation": pred.explanation,
        }

    answer = await agents.chat_agent(body.message, context)
    db.add(Message(conversation_id=convo.id, role="assistant", content=answer))
    await record_usage(db, user.id, "chat", resource_type="property", resource_id=str(property_id))
    await db.flush()

    result = await db.execute(
        select(AIConversation)
        .options(selectinload(AIConversation.messages))
        .where(AIConversation.id == convo.id)
    )
    convo = result.scalar_one()
    return ChatResponse(
        conversation_id=convo.id,
        messages=[MessageOut.model_validate(m) for m in sorted(convo.messages, key=lambda x: x.created_at)],
    )


@router.get("/properties/{property_id}/chat", response_model=list[ChatResponse])
async def list_conversations(
    property_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AIConversation)
        .options(selectinload(AIConversation.messages))
        .where(AIConversation.property_id == property_id, AIConversation.user_id == user.id)
        .order_by(AIConversation.created_at.desc())
    )
    out = []
    for c in result.scalars().all():
        out.append(
            ChatResponse(
                conversation_id=c.id,
                messages=[MessageOut.model_validate(m) for m in sorted(c.messages, key=lambda x: x.created_at)],
            )
        )
    return out
