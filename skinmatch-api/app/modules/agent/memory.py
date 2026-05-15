from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.modules.agent.models import AgentMessage


def save_message(
    db: Session,
    *,
    user_id: UUID,
    role: str,
    content: str,
    intent: str | None = None,
    confidence: str | None = None,
    tools_used: list[str] | None = None,
    structured_result: Any | None = None,
    user_context_snapshot: Any | None = None,
) -> AgentMessage:
    message = AgentMessage(
        user_id=user_id,
        role=role,
        content=content,
        intent=intent,
        confidence=confidence,
        tools_used=tools_used or [],
        structured_result=jsonable_encoder(structured_result) if structured_result is not None else None,
        user_context_snapshot=jsonable_encoder(user_context_snapshot) if user_context_snapshot is not None else None,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, user_id: UUID, limit: int = 10) -> list[AgentMessage]:
    statement = (
        select(AgentMessage)
        .where(AgentMessage.user_id == user_id)
        .order_by(desc(AgentMessage.created_at))
        .limit(limit)
    )
    return list(reversed(db.scalars(statement).all()))


def get_conversation_summary(db: Session, user_id: UUID) -> dict[str, Any]:
    messages = get_recent_messages(db, user_id, limit=10)
    products: list[str] = []
    problems: list[str] = []
    decisions: list[str] = []
    goals: list[str] = []

    for message in messages:
        content = message.content.lower()
        structured = message.structured_result if isinstance(message.structured_result, dict) else {}
        if structured.get("product_id") and structured.get("verdict"):
            decisions.append(f"Produto analisado com veredito {structured.get('verdict')}.")
        if "rotina" in content:
            goals.append("rotina")
        if "acne" in content:
            goals.append("acne")
        if "ard" in content or "irrit" in content or "vermelh" in content:
            problems.append(message.content[:160])
        if isinstance(structured, dict) and structured.get("product_id"):
            product_name = structured.get("product_name") or "produto analisado"
            products.append(str(product_name))

    return {
        "current_goal": goals[-1] if goals else None,
        "products_discussed": products[-5:],
        "recent_problems": problems[-3:],
        "decisions_made": decisions[-5:],
    }
