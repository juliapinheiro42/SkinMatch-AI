from collections import Counter
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analysis.schemas import PersonalInsightsResponse
from app.modules.analysis_records.repository import list_records_with_feedback
from app.modules.personalization.service import (
    affinity_for_engine,
    confidence_label,
    get_problematic_ingredients,
    get_user_affinity,
    get_well_tolerated_ingredients,
)


def _ingredient_names(parsed_formula_snapshot: list[dict]) -> list[str]:
    return [
        str(item.get("inci_name", "")).strip().lower()
        for item in parsed_formula_snapshot
        if str(item.get("inci_name", "")).strip()
    ]


def get_personal_insights(db: Session, user_id: UUID) -> PersonalInsightsResponse:
    records = list_records_with_feedback(db, user_id)
    trigger_counts: Counter[str] = Counter()
    tolerated_counts: Counter[str] = Counter()

    for record in records:
        if not record.feedback:
            continue

        ingredients = _ingredient_names(record.parsed_formula_snapshot)

        if record.feedback.irritation_level >= 3:
            trigger_counts.update(ingredients)

        if record.feedback.satisfaction_level >= 4 and record.feedback.irritation_level <= 1:
            tolerated_counts.update(ingredients)

    common_triggers = [
        {"ingredient": ingredient, "reaction": "irritation", "occurrences": count}
        for ingredient, count in trigger_counts.most_common()
    ]
    well_tolerated_ingredients = [
        {"ingredient": ingredient, "positive_feedbacks": count}
        for ingredient, count in tolerated_counts.most_common()
    ]

    patterns: list[str] = []
    for item in common_triggers[:3]:
        patterns.append(
            f"Produtos com {item['ingredient']} aparecem associados a irritacao em seus feedbacks."
        )
    for item in well_tolerated_ingredients[:3]:
        patterns.append(
            f"Produtos com {item['ingredient']} tiveram boa satisfacao media."
        )

    try:
        problematic = get_problematic_ingredients(db, user_id)
        well_tolerated_affinity = get_well_tolerated_ingredients(db, user_id)
        low_confidence = [
            {
                "ingredient_name": item.ingredient_name,
                "tolerance_score": item.tolerance_score,
                "confidence": item.confidence,
                "feedback_count": item.irritation_count + item.acne_count + item.positive_count + item.neutral_count,
                "confidence_label": confidence_label(item.confidence),
            }
            for item in get_user_affinity(db, user_id)
            if 0 < item.confidence < 0.4
        ]
    except Exception:
        problematic = []
        well_tolerated_affinity = []
        low_confidence = []

    return PersonalInsightsResponse(
        total_feedbacks=len(records),
        common_triggers=common_triggers,
        well_tolerated_ingredients=well_tolerated_ingredients,
        patterns=patterns,
        ingredient_affinity={
            "problematic": problematic,
            "well_tolerated": well_tolerated_affinity,
            "low_confidence": low_confidence,
        },
    )


def insights_for_engine(db: Session, user_id: UUID) -> dict:
    insights = get_personal_insights(db, user_id)
    engine_insights = {
        "common_triggers": {item.ingredient for item in insights.common_triggers},
        "well_tolerated_ingredients": {item.ingredient for item in insights.well_tolerated_ingredients},
    }
    try:
        engine_insights["ingredient_affinity"] = affinity_for_engine(db, user_id)
    except Exception:
        engine_insights["ingredient_affinity"] = {}
    return engine_insights
