from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analysis.engine import analyze_formula
from app.modules.ingredients.repository import list_ingredients
from app.modules.insights.service import insights_for_engine
from app.modules.personalization.service import affinity_for_engine
from app.modules.products.models import Product
from app.modules.products.repository import list_products_with_formulas
from app.modules.recommendations.ranking import GOAL_INGREDIENTS
from app.modules.recommendations.ranking_v3 import rank_recommendations_v3
from app.modules.recommendations.schemas import RecommendationItem, RecommendationRequest


TEMP_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _normalized(values: list[str]) -> set[str]:
    return {value.strip().lower().removesuffix(".") for value in values if value.strip()}


def _snapshot_for_product(product: Product) -> list[dict[str, Any]]:
    if product.formulas:
        return product.formulas[0].parsed_formula_snapshot
    return []


def _hydrate_snapshot(snapshot: list[dict[str, Any]], ingredient_lookup: dict[str, Any]) -> list[dict[str, Any]]:
    hydrated = []
    for item in snapshot:
        name = str(item.get("inci_name", "")).strip().lower().removesuffix(".")
        ingredient = ingredient_lookup.get(name)
        hydrated.append(
            {
                **item,
                "inci_name": name,
                "unknown": ingredient is None or bool(item.get("unknown", False)),
                "ingredient": ingredient,
            }
        )
    return hydrated


def _ingredient_names(snapshot: list[dict[str, Any]]) -> list[str]:
    return [
        str(item.get("inci_name", "")).strip().lower().removesuffix(".")
        for item in snapshot
        if str(item.get("inci_name", "")).strip()
    ]


def _contains_blocked_ingredient(ingredient_names: list[str], blocked: set[str]) -> bool:
    return bool(_normalized(ingredient_names) & blocked)


def _percent(value: float | int) -> int:
    number = float(value)
    if number <= 1:
        number *= 100
    return max(0, min(100, round(number)))


def generate_reason(product_analysis: dict, skin_profile, main_goal: str) -> str:
    if product_analysis.get("reason"):
        return product_analysis["reason"]
    ingredients = _normalized(product_analysis.get("ingredient_names", []))
    tolerated = _normalized(skin_profile.tolerated_ingredients)
    goal_ingredients = GOAL_INGREDIENTS.get(main_goal, set())
    personal_problematic = product_analysis.get("personal_problematic_ingredients", [])
    personal_tolerated = product_analysis.get("personal_well_tolerated_ingredients", [])

    if personal_problematic:
        return (
            "Boa opcao apenas com cautela: contem ingrediente que aparece como possivel gatilho no seu historico"
        )
    if personal_tolerated:
        ingredient = personal_tolerated[0]
        return (
            f"Recomendado porque evita seus principais gatilhos e contem {ingredient}, "
            "que aparece como bem tolerado no seu historico"
        )

    if product_analysis["irritation_risk"] <= 30 and product_analysis["benefit_score"] >= 70:
        return "Alta compatibilidade com seu perfil e baixo risco de irritacao"
    if main_goal == "acne" and ingredients & GOAL_INGREDIENTS["acne"]:
        return "Contem ativos que ajudam no controle da acne"
    if main_goal == "barrier" and ingredients & GOAL_INGREDIENTS["barrier"]:
        return "Ajuda a reforcar a barreira da pele"
    if ingredients & tolerated:
        return "Inclui ingredientes que sua pele costuma tolerar bem"
    return "Boa compatibilidade geral com os criterios informados"


def key_ingredients(product_analysis: dict, main_goal: str) -> list[str]:
    positives = list(product_analysis.get("positive_ingredients", []))
    ingredients = _normalized(product_analysis.get("ingredient_names", []))
    goal_matches = [ingredient for ingredient in GOAL_INGREDIENTS.get(main_goal, set()) if ingredient in ingredients]
    ordered = goal_matches + positives
    unique = []
    for ingredient in ordered:
        if ingredient not in unique:
            unique.append(ingredient)
    return unique[:3]


def recommendation_analyses(db: Session, request: RecommendationRequest) -> list[dict]:
    products = list_products_with_formulas(db, limit=100)
    ingredients = list_ingredients(db)
    ingredient_lookup = {ingredient.inci_name.lower(): ingredient for ingredient in ingredients}
    personal_insights = insights_for_engine(db, TEMP_USER_ID)
    affinity = affinity_for_engine(db, TEMP_USER_ID)
    problematic = {
        ingredient
        for ingredient, data in affinity.items()
        if data.get("confidence", 0) >= 0.4 and data.get("tolerance_score", 0) <= -0.5
    }
    well_tolerated = {
        ingredient
        for ingredient, data in affinity.items()
        if data.get("confidence", 0) >= 0.4 and data.get("tolerance_score", 0) >= 0.5
    }
    blocked = _normalized(request.exclude_ingredients) | _normalized(request.skin_profile.known_triggers)
    analyses: list[dict] = []

    for product in products:
        if hasattr(product, "raw_ingredient_list") and not product.raw_ingredient_list:
            continue
        snapshot = _snapshot_for_product(product)
        ingredient_names = _ingredient_names(snapshot)

        if not snapshot or _contains_blocked_ingredient(ingredient_names, blocked):
            continue

        parsed = _hydrate_snapshot(snapshot, ingredient_lookup)
        result = analyze_formula(parsed, request.skin_profile, personal_insights=personal_insights)
        ingredient_set = _normalized(ingredient_names)
        personal_problematic = sorted(ingredient_set & problematic)
        personal_well_tolerated = sorted(ingredient_set & well_tolerated)
        analysis = {
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": getattr(product, "category", None),
            "routine_step": getattr(product, "routine_step", None),
            "usage_periods": getattr(product, "usage_periods", []) or [],
            "price_range": getattr(product, "price_range", None),
            "tags": getattr(product, "tags", []) or [],
            "catalog_status": getattr(product, "catalog_status", "active"),
            "is_active_treatment": getattr(product, "is_active_treatment", False),
            "is_sunscreen": getattr(product, "is_sunscreen", False),
            "is_moisturizer": getattr(product, "is_moisturizer", False),
            "is_cleanser": getattr(product, "is_cleanser", False),
            "compatibility_score": _percent(result["compatibility_score"]),
            "irritation_risk": _percent(result["irritation_risk"]),
            "acne_risk": _percent(result["acne_risk"]),
            "benefit_score": _percent(result["benefit_score"]),
            "positive_ingredients": result["positive_ingredients"],
            "ingredient_names": ingredient_names,
            "personal_problematic_ingredients": personal_problematic,
            "personal_well_tolerated_ingredients": personal_well_tolerated,
        }

        if analysis["irritation_risk"] > 95:
            continue

        analyses.append(analysis)

    request_constraints = getattr(request, "constraints", None)
    constraints = request_constraints.model_dump() if hasattr(request_constraints, "model_dump") else dict(request_constraints or {})
    constraints["exclude_ingredients"] = sorted(blocked)
    return rank_recommendations_v3(
        analyses,
        request.skin_profile,
        request.main_goal,
        affinity,
        constraints,
    )


def recommend_products(db: Session, request: RecommendationRequest) -> list[RecommendationItem]:
    ranked = recommendation_analyses(db, request)
    return [
        RecommendationItem(
            product_id=item["product_id"],
            name=item["name"],
            brand=item["brand"],
            category=item.get("category"),
            compatibility_score=item["compatibility_score"],
            irritation_risk=item["irritation_risk"],
            acne_risk=item["acne_risk"],
            benefit_score=item["benefit_score"],
            final_score=item["final_score"],
            score_breakdown=item["score_breakdown"],
            reason_codes=item["reason_codes"],
            reason=generate_reason(item, request.skin_profile, request.main_goal),
            key_ingredients=key_ingredients(item, request.main_goal),
        )
        for item in ranked[: request.limit]
    ]
