from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analysis_records.repository import get_analysis_record
from app.modules.personalization.models import UserIngredientAffinity
from app.modules.personalization.repository import get_affinity_by_ingredient, list_user_affinity, upsert_affinity
from app.modules.personalization.schemas import IngredientAffinitySummary


def _ingredient_names(parsed_formula_snapshot: list[dict[str, Any]]) -> list[str]:
    names = []
    for item in parsed_formula_snapshot:
        name = str(item.get("inci_name", "")).strip().lower().removesuffix(".")
        if name and name not in names:
            names.append(name)
    return names


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def _confidence(total: int) -> float:
    if total <= 0:
        return 0.0
    if total == 1:
        return 0.25
    if total <= 3:
        return 0.6
    return 0.9


def confidence_label(confidence: float) -> str:
    if confidence < 0.4:
        return "baixa"
    if confidence < 0.75:
        return "media"
    return "alta"


def _total(affinity: UserIngredientAffinity) -> int:
    return affinity.irritation_count + affinity.acne_count + affinity.positive_count + affinity.neutral_count


def _feedback_delta(feedback: Any) -> tuple[float, dict[str, int]]:
    counts = {"irritation_count": 0, "acne_count": 0, "positive_count": 0, "neutral_count": 0}
    delta = 0.0

    if feedback.irritation_level >= 3:
        delta -= 0.35
        counts["irritation_count"] += 1
    if feedback.acne_level >= 3:
        delta -= 0.25
        counts["acne_count"] += 1
    if feedback.satisfaction_level >= 4 and feedback.irritation_level <= 1:
        delta += 0.25
        counts["positive_count"] += 1

    if not any(counts.values()):
        counts["neutral_count"] += 1
        delta += 0.02

    return delta, counts


def update_affinity_from_feedback(db: Session, user_id: UUID, analysis_id: UUID, feedback: Any) -> None:
    record = get_analysis_record(db, user_id, analysis_id)
    if record is None:
        return

    ingredients = _ingredient_names(record.parsed_formula_snapshot)
    delta, count_updates = _feedback_delta(feedback)
    now = datetime.now(timezone.utc)

    for ingredient in ingredients:
        affinity = get_affinity_by_ingredient(db, user_id, ingredient)
        if affinity is None:
            affinity = UserIngredientAffinity(
                user_id=user_id,
                ingredient_name=ingredient,
                tolerance_score=0.0,
                irritation_count=0,
                acne_count=0,
                positive_count=0,
                neutral_count=0,
                confidence=0.0,
                last_seen_at=now,
            )

        affinity.tolerance_score = round(_clamp(affinity.tolerance_score + delta), 3)
        affinity.irritation_count += count_updates["irritation_count"]
        affinity.acne_count += count_updates["acne_count"]
        affinity.positive_count += count_updates["positive_count"]
        affinity.neutral_count += count_updates["neutral_count"]
        affinity.confidence = _confidence(_total(affinity))
        affinity.last_seen_at = now
        upsert_affinity(db, affinity)


def get_user_affinity(db: Session, user_id: UUID) -> list[UserIngredientAffinity]:
    try:
        return list_user_affinity(db, user_id)
    except Exception:
        if hasattr(db, "rollback"):
            db.rollback()
        return []


def get_problematic_ingredients(db: Session, user_id: UUID) -> list[IngredientAffinitySummary]:
    return [
        IngredientAffinitySummary(
            ingredient_name=item.ingredient_name,
            tolerance_score=item.tolerance_score,
            confidence=item.confidence,
            feedback_count=_total(item),
            confidence_label=confidence_label(item.confidence),
        )
        for item in list_user_affinity(db, user_id)
        if item.tolerance_score <= -0.3
    ]


def get_well_tolerated_ingredients(db: Session, user_id: UUID) -> list[IngredientAffinitySummary]:
    return [
        IngredientAffinitySummary(
            ingredient_name=item.ingredient_name,
            tolerance_score=item.tolerance_score,
            confidence=item.confidence,
            feedback_count=_total(item),
            confidence_label=confidence_label(item.confidence),
        )
        for item in list_user_affinity(db, user_id)
        if item.tolerance_score >= 0.3
    ]


def affinity_for_engine(db: Session, user_id: UUID) -> dict[str, dict[str, float]]:
    try:
        items = list_user_affinity(db, user_id)
    except Exception:
        if hasattr(db, "rollback"):
            db.rollback()
        return {}
    return {
        item.ingredient_name: {
            "tolerance_score": item.tolerance_score,
            "confidence": item.confidence,
        }
        for item in items
    }


def apply_personalization_to_analysis(analysis_result: dict, affinity: dict[str, dict[str, float]]) -> dict:
    result = {**analysis_result}
    problematic = [name for name, data in affinity.items() if data["tolerance_score"] <= -0.5]
    tolerated = [name for name, data in affinity.items() if data["tolerance_score"] >= 0.5]
    result["personalization"] = {
        "problematic_ingredients": problematic,
        "well_tolerated_ingredients": tolerated,
    }
    return result
