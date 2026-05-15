from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.feedback.models import ProductFeedback


def get_feedback_by_analysis(db: Session, user_id: UUID, analysis_id: UUID) -> ProductFeedback | None:
    statement = select(ProductFeedback).where(
        ProductFeedback.user_id == user_id,
        ProductFeedback.analysis_id == analysis_id,
    )
    return db.scalar(statement)


def upsert_feedback(
    db: Session,
    user_id: UUID,
    analysis_id: UUID,
    payload: dict,
) -> ProductFeedback:
    feedback = get_feedback_by_analysis(db, user_id, analysis_id)

    if feedback is None:
        feedback = ProductFeedback(user_id=user_id, analysis_id=analysis_id, **payload)
        db.add(feedback)
    else:
        for key, value in payload.items():
            setattr(feedback, key, value)

    db.commit()
    db.refresh(feedback)
    return feedback
