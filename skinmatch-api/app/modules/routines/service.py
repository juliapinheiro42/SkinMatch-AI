from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.recommendations.schemas import RecommendationRequest
from app.modules.recommendations.service import recommendation_analyses
from app.modules.personalization.service import affinity_for_engine
from app.modules.routines.rules import (
    AHA_BHA,
    HEAVY_OILS,
    generate_step_instructions,
    generate_step_reason,
    has_conflicting_actives,
    infer_product_type,
    normalized,
    routine_order,
    routine_warnings,
)
from app.modules.routines.schemas import RoutineProduct, RoutineRequest, RoutineResponse, RoutineStep


def _with_type(products: list[dict]) -> list[dict]:
    return [{**product, "routine_type": infer_product_type(product)} for product in products]


def _avoid_for_goal(product: dict, main_goal: str) -> bool:
    ingredients = normalized(product.get("ingredient_names", []))
    return main_goal == "acne" and bool(ingredients & HEAVY_OILS)


def _safe_to_add(selected: list[dict], candidate: dict) -> bool:
    return not has_conflicting_actives(selected + [candidate])


def is_complete_routine(morning: list[dict]) -> bool:
    required = {"cleanser", "moisturizer", "sunscreen"}
    return required.issubset({product.get("routine_type") for product in morning})


TEMP_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _affinity_sets(affinity: dict | None) -> tuple[set[str], set[str]]:
    if not affinity:
        return set(), set()
    problematic = {
        ingredient
        for ingredient, data in affinity.items()
        if data.get("confidence", 0) >= 0.4 and data.get("tolerance_score", 0) <= -0.5
    }
    tolerated = {
        ingredient
        for ingredient, data in affinity.items()
        if data.get("confidence", 0) >= 0.4 and data.get("tolerance_score", 0) >= 0.5
    }
    return problematic, tolerated


def _contains_any(product: dict, ingredients: set[str]) -> bool:
    return bool(normalized(product.get("ingredient_names", [])) & ingredients)


def select_best_products_for_routine(
    products: list[dict],
    skin_profile,
    goal: str,
    max_steps: int,
    affinity: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    problematic, tolerated = _affinity_sets(affinity)
    available = [product for product in _with_type(products) if not _avoid_for_goal(product, goal)]
    available = [
        product
        for product in available
        if not (product.get("routine_type") == "treatment" and _contains_any(product, problematic))
    ]
    if skin_profile.sensitive_skin:
        available = sorted(
            available,
            key=lambda item: (item["irritation_risk"], -item["benefit_score"], -item["compatibility_score"]),
        )
        max_steps = min(max_steps, 4)

    used_ids: set[str] = set()

    def pick(step_type: str, selected: list[dict]) -> dict | None:
        candidates = [
            product
            for product in available
            if product["routine_type"] == step_type
            and str(product["product_id"]) not in used_ids
            and _safe_to_add(selected, product)
        ]
        if not candidates:
            return None
        candidates = sorted(
            candidates,
            key=lambda item: (
                item["ranking_score"] + (6 if _contains_any(item, tolerated) else 0) - (12 if _contains_any(item, problematic) else 0)
            ),
            reverse=True,
        )
        chosen = candidates[0]
        used_ids.add(str(chosen["product_id"]))
        return chosen

    morning: list[dict] = []
    night: list[dict] = []

    morning_order = ["cleanser", "moisturizer", "sunscreen"] if skin_profile.sensitive_skin else ["cleanser", "moisturizer", "sunscreen"]
    for step_type in morning_order:
        if len(morning) >= max_steps:
            break
        chosen = pick(step_type, morning)
        if chosen:
            morning.append(chosen)

    if not any(product["routine_type"] == "sunscreen" for product in morning):
        sunscreen = pick("sunscreen", morning)
        if sunscreen and len(morning) < max_steps:
            morning.append(sunscreen)

    if not is_complete_routine(morning):
        missing = [
            step_type
            for step_type in ["cleanser", "moisturizer", "sunscreen"]
            if not any(product["routine_type"] == step_type for product in morning)
        ]
        for step_type in missing:
            if len(morning) >= max_steps:
                break
            chosen = pick(step_type, morning)
            if chosen:
                morning.append(chosen)

    for step_type in routine_order("night"):
        if len(night) >= max_steps:
            break
        chosen = pick(step_type, night)
        if chosen:
            night.append(chosen)

    if skin_profile.sensitive_skin:
        for routine in (morning, night):
            strong_seen = False
            filtered = []
            for product in routine:
                ingredients = normalized(product.get("ingredient_names", []))
                has_strong = bool(ingredients & (AHA_BHA | {"retinol", "retinal", "benzoyl peroxide"}))
                if has_strong and strong_seen:
                    continue
                strong_seen = strong_seen or has_strong
                filtered.append(product)
            routine[:] = filtered

    return morning[:max_steps], night[:max_steps]


def _to_steps(products: list[dict], period: str, skin_profile, main_goal: str) -> list[RoutineStep]:
    order = routine_order(period)
    products = sorted(products, key=lambda item: order.index(item["routine_type"]) if item["routine_type"] in order else 99)
    return [
        RoutineStep(
            step=index,
            type=product["routine_type"],
            product=RoutineProduct(id=product["product_id"], name=product["name"], brand=product["brand"]),
            instructions=generate_step_instructions(product["routine_type"], product, skin_profile),
            reason=generate_step_reason(product["routine_type"], product, skin_profile, main_goal),
        )
        for index, product in enumerate(products, start=1)
    ]


def generate_routine(db: Session, request: RoutineRequest) -> RoutineResponse:
    recommendations = recommendation_analyses(
        db,
        RecommendationRequest(
            skin_profile=request.skin_profile,
            main_goal=request.main_goal,
            exclude_ingredients=request.constraints.avoid_ingredients,
            limit=20,
        ),
    )
    morning_products, night_products = select_best_products_for_routine(
        recommendations,
        request.skin_profile,
        request.main_goal,
        request.constraints.max_steps,
        affinity_for_engine(db, TEMP_USER_ID),
    )
    problematic, _ = _affinity_sets(affinity_for_engine(db, TEMP_USER_ID))
    personalized_warnings = []
    selected_products = morning_products + night_products
    selected_problematic = sorted(
        {
            ingredient
            for product in selected_products
            for ingredient in normalized(product.get("ingredient_names", []))
            if ingredient in problematic
        }
    )
    if selected_problematic:
        personalized_warnings.append(
            "Esta rotina contem ingrediente com tolerancia negativa no seu historico: "
            + ", ".join(selected_problematic[:3])
            + ". Introduza com cautela."
        )
    return RoutineResponse(
        morning_routine=_to_steps(morning_products, "morning", request.skin_profile, request.main_goal),
        night_routine=_to_steps(night_products, "night", request.skin_profile, request.main_goal),
        warnings=routine_warnings(morning_products, night_products, request.skin_profile) + personalized_warnings,
    )
