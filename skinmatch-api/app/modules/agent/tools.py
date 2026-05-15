from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analysis.engine import analyze_formula
from app.modules.analysis.parser import parse_formula
from app.modules.analysis.schemas import AnalysisHistoryItem, AnalysisRequest
from app.modules.analysis_records.models import AnalysisRecord
from app.modules.analysis_records.repository import create_analysis_record, list_analysis_records
from app.modules.formula_cache.service import get_or_create_formula_cache
from app.modules.formulas.service import formula_hash, normalize_formula_text
from app.modules.ingredients.repository import list_ingredients
from app.modules.insights.service import get_personal_insights, insights_for_engine
from app.modules.products.product_service import get_or_create_product_for_formula
from app.modules.recommendations.schemas import RecommendationRequest
from app.modules.recommendations.service import recommend_products
from app.modules.routines.schemas import RoutineConstraints, RoutineRequest
from app.modules.routines.service import generate_routine
from app.modules.skin_profiles.schemas import SkinProfileInput


def default_skin_profile() -> SkinProfileInput:
    return SkinProfileInput(
        skin_type="oily",
        sensitive_skin=True,
        acne_prone=True,
        barrier_compromised=False,
        known_triggers=[],
        tolerated_ingredients=[],
    )


def resolve_skin_profile(db: Session, user_id: UUID, provided: SkinProfileInput | None = None) -> SkinProfileInput:
    if provided:
        return provided

    latest = list_analysis_records(db, user_id=user_id, limit=1)
    if latest:
        try:
            return SkinProfileInput.model_validate(latest[0].skin_profile_snapshot)
        except Exception:
            pass

    return default_skin_profile()


def _parsed_snapshot(parsed: list[dict]) -> list[dict]:
    return [{key: value for key, value in item.items() if key != "ingredient"} for item in parsed]


def _analysis_output(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "analysis_id": result["analysis_id"],
        "product_id": result["product_id"],
        "compatibility_score": result["compatibility_score"],
        "verdict": result["verdict"],
        "irritation_risk": result["irritation_risk"],
        "acne_risk": result["acne_risk"],
        "benefit_score": result["benefit_score"],
        "barrier_support": result["barrier_support"],
        "applied_rules": result["applied_rules"],
        "positive_ingredients": result["positive_ingredients"],
        "warning_ingredients": result["warning_ingredients"],
        "unknown_ingredients": result["unknown_ingredients"],
        "recommendation": result["recommendation"],
        "disclaimer": result["disclaimer"],
    }


def analyze_product_tool(
    db: Session,
    *,
    user_id: UUID,
    raw_ingredient_list: str,
    product_name: str | None = None,
    brand: str | None = None,
    main_goal: str = "general",
    skin_profile: SkinProfileInput | None = None,
) -> dict[str, Any]:
    profile = resolve_skin_profile(db, user_id, skin_profile)
    request = AnalysisRequest(
        raw_ingredient_list=raw_ingredient_list,
        skin_profile=profile,
        main_goal=main_goal,
        product_name=product_name,
        brand=brand,
    )
    ingredients = list_ingredients(db)
    normalized_formula = normalize_formula_text(request.formula_text)
    parsed = parse_formula(normalized_formula, ingredients)
    parsed_snapshot = _parsed_snapshot(parsed)
    product = get_or_create_product_for_formula(
        db,
        raw_ingredient_list=normalized_formula,
        parsed_formula_snapshot=parsed_snapshot,
        product_name=product_name,
        brand=brand,
    )
    cache = get_or_create_formula_cache(db, formula_hash(normalized_formula), parsed)
    result = analyze_formula(
        parsed,
        profile,
        personal_insights=insights_for_engine(db, user_id),
        base_cache={
            "base_irritation_risk": cache.base_irritation_risk,
            "base_acne_risk": cache.base_acne_risk,
            "base_benefit_score": cache.base_benefit_score,
            "base_barrier_support": cache.base_barrier_support,
        },
    )
    record = create_analysis_record(
        db,
        AnalysisRecord(
            user_id=user_id,
            product_id=product.id,
            product_name=product_name,
            brand=brand,
            main_goal=main_goal,
            raw_ingredient_list=normalized_formula,
            skin_profile_snapshot=profile.model_dump(mode="json"),
            parsed_formula_snapshot=parsed_snapshot,
            compatibility_score=result["compatibility_score"],
            verdict=result["verdict"],
            irritation_risk=result["irritation_risk"],
            acne_risk=result["acne_risk"],
            benefit_score=result["benefit_score"],
            barrier_support=result["barrier_support"],
            applied_rules=result["applied_rules"],
            positive_ingredients=result["positive_ingredients"],
            warning_ingredients=result["warning_ingredients"],
            unknown_ingredients=result["unknown_ingredients"],
            recommendation=result["recommendation"],
            disclaimer=result["disclaimer"],
        ),
    )
    result["analysis_id"] = record.id
    result["product_id"] = product.id
    return _analysis_output(result)


def recommend_products_tool(
    db: Session,
    *,
    user_id: UUID,
    main_goal: str,
    exclude_ingredients: list[str] | None = None,
    constraints: dict[str, Any] | None = None,
    limit: int = 5,
    skin_profile: SkinProfileInput | None = None,
) -> list[dict[str, Any]]:
    profile = resolve_skin_profile(db, user_id, skin_profile)
    recommendations = recommend_products(
        db,
        RecommendationRequest(
            skin_profile=profile,
            main_goal=main_goal,
            exclude_ingredients=exclude_ingredients or [],
            constraints=constraints or {},
            limit=limit,
        ),
    )
    return [item.model_dump(mode="json") for item in recommendations]


def generate_routine_tool(
    db: Session,
    *,
    user_id: UUID,
    main_goal: str,
    constraints: dict[str, Any] | None = None,
    skin_profile: SkinProfileInput | None = None,
) -> dict[str, Any]:
    profile = resolve_skin_profile(db, user_id, skin_profile)
    payload = constraints or {}
    routine = generate_routine(
        db,
        RoutineRequest(
            skin_profile=profile,
            main_goal=main_goal,
            constraints=RoutineConstraints(
                avoid_ingredients=payload.get("avoid_ingredients", []),
                max_steps=payload.get("max_steps", 5),
            ),
        ),
    )
    return routine.model_dump(mode="json")


def get_personal_insights_tool(db: Session, *, user_id: UUID) -> dict[str, Any]:
    return get_personal_insights(db, user_id).model_dump(mode="json")


def get_analysis_history_tool(db: Session, *, user_id: UUID, limit: int = 5) -> list[dict[str, Any]]:
    records = list_analysis_records(db, user_id=user_id, limit=limit)
    return [
        AnalysisHistoryItem(
            analysis_id=record.id,
            product_id=record.product_id,
            product_name=record.product_name,
            brand=record.brand,
            main_goal=record.main_goal,
            compatibility_score=record.compatibility_score,
            verdict=record.verdict,
            irritation_risk=record.irritation_risk,
            acne_risk=record.acne_risk,
            benefit_score=record.benefit_score,
            created_at=record.created_at,
        ).model_dump(mode="json")
        for record in records
    ]


def get_current_routine_tool(db: Session, *, user_id: UUID) -> dict[str, Any]:
    records = list_analysis_records(db, user_id=user_id, limit=10)
    for record in records:
        if record.main_goal:
            return {
                "source": "recent_analysis",
                "main_goal": record.main_goal,
                "product_name": record.product_name,
                "brand": record.brand,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
    return {"source": "none", "routine": None}


def adjust_routine_tool(
    db: Session,
    *,
    user_id: UUID,
    main_goal: str,
    constraints: dict[str, Any] | None = None,
    skin_profile: SkinProfileInput | None = None,
) -> dict[str, Any]:
    return generate_routine_tool(
        db,
        user_id=user_id,
        main_goal=main_goal,
        constraints=constraints,
        skin_profile=skin_profile,
    )
