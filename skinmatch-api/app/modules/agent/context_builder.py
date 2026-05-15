from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.agent.memory import get_conversation_summary
from app.modules.analysis_records.repository import list_analysis_records, list_records_with_feedback
from app.modules.insights.service import get_personal_insights
from app.modules.personalization.service import confidence_label, get_user_affinity
from app.modules.skin_profiles.schemas import SkinProfileInput


def _compact_analysis(record) -> dict[str, Any]:
    return {
        "analysis_id": str(record.id),
        "product_id": str(record.product_id) if record.product_id else None,
        "product_name": record.product_name,
        "brand": record.brand,
        "main_goal": record.main_goal,
        "compatibility_score": record.compatibility_score,
        "verdict": record.verdict,
        "warning_ingredients": record.warning_ingredients[:5],
        "positive_ingredients": record.positive_ingredients[:5],
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def _compact_feedback(record) -> dict[str, Any] | None:
    if not record.feedback:
        return None
    return {
        "product_name": record.product_name,
        "brand": record.brand,
        "irritation_level": record.feedback.irritation_level,
        "acne_level": record.feedback.acne_level,
        "dryness_level": record.feedback.dryness_level,
        "satisfaction_level": record.feedback.satisfaction_level,
        "noticed_benefits": record.feedback.noticed_benefits[:5],
        "comments": record.feedback.comments,
    }


def build_agent_context(
    db: Session,
    user_id: UUID,
    provided_skin_profile: SkinProfileInput | None = None,
) -> dict[str, Any]:
    recent_records = list_analysis_records(db, user_id=user_id, limit=10)
    feedback_records = list_records_with_feedback(db, user_id)[:10]
    insights = get_personal_insights(db, user_id)
    skin_profile = provided_skin_profile

    if skin_profile is None and recent_records:
        try:
            skin_profile = SkinProfileInput.model_validate(recent_records[0].skin_profile_snapshot)
        except Exception:
            skin_profile = None

    feedbacks = [item for item in (_compact_feedback(record) for record in feedback_records) if item]
    recent_reactions = [
        item
        for item in feedbacks
        if item["irritation_level"] >= 2 or item["acne_level"] >= 2 or item["dryness_level"] >= 2
    ][:5]

    known_triggers = set(skin_profile.known_triggers if skin_profile else [])
    known_triggers.update(item.ingredient for item in insights.common_triggers[:5])
    tolerated = set(skin_profile.tolerated_ingredients if skin_profile else [])
    tolerated.update(item.ingredient for item in insights.well_tolerated_ingredients[:5])
    affinity_items = get_user_affinity(db, user_id)
    affinity_context = {
        "problematic": [
            {
                "ingredient_name": item.ingredient_name,
                "tolerance_score": item.tolerance_score,
                "confidence": item.confidence,
                "confidence_label": confidence_label(item.confidence),
            }
            for item in affinity_items
            if item.tolerance_score <= -0.3
        ][:10],
        "well_tolerated": [
            {
                "ingredient_name": item.ingredient_name,
                "tolerance_score": item.tolerance_score,
                "confidence": item.confidence,
                "confidence_label": confidence_label(item.confidence),
            }
            for item in affinity_items
            if item.tolerance_score >= 0.3
        ][:10],
        "low_confidence": [
            {
                "ingredient_name": item.ingredient_name,
                "tolerance_score": item.tolerance_score,
                "confidence": item.confidence,
                "confidence_label": confidence_label(item.confidence),
            }
            for item in affinity_items
            if 0 < item.confidence < 0.4
        ][:10],
    }

    context_status = "available" if recent_records or feedback_records else "insufficient_history"
    return {
        "skin_profile": skin_profile.model_dump(mode="json") if skin_profile else None,
        "personal_insights": insights.model_dump(mode="json"),
        "recent_analysis": [_compact_analysis(record) for record in recent_records[:10]],
        "recent_feedbacks": feedbacks[:10],
        "current_routine": None,
        "known_triggers": sorted(known_triggers),
        "tolerated_ingredients": sorted(tolerated),
        "ingredient_affinity": affinity_context,
        "recent_reactions": recent_reactions,
        "recent_products_used": [
            item["product_name"]
            for item in feedbacks
            if item.get("product_name")
        ][:10],
        "user_goals": list({record.main_goal for record in recent_records if record.main_goal})[:5],
        "conversation_summary": get_conversation_summary(db, user_id),
        "context_status": context_status,
    }
