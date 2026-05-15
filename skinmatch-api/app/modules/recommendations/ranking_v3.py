from typing import Any

from app.modules.skin_profiles.schemas import SkinProfileInput


GOAL_WEIGHTS = {
    "acne": {
        "salicylic acid": 25,
        "azelaic acid": 25,
        "niacinamide": 20,
        "zinc pca": 15,
        "benzoyl peroxide": 20,
    },
    "oil_control": {
        "niacinamide": 25,
        "zinc pca": 25,
        "salicylic acid": 20,
    },
    "barrier": {
        "ceramide": 30,
        "panthenol": 25,
        "glycerin": 15,
        "hyaluronic acid": 15,
    },
    "hyperpigmentation": {
        "sunscreen": 30,
        "niacinamide": 20,
        "ascorbic acid": 20,
        "azelaic acid": 20,
    },
}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> int:
    return round(max(minimum, min(maximum, value)))


def _normalized(values: Any) -> set[str]:
    if not values:
        return set()
    return {str(value).strip().lower().removesuffix(".") for value in values if str(value).strip()}


def _constraint(constraints: Any, key: str, default: Any = None) -> Any:
    if constraints is None:
        return default
    if isinstance(constraints, dict):
        return constraints.get(key, default)
    return getattr(constraints, key, default)


def product_category(product: dict) -> str:
    category = str(product.get("category") or product.get("routine_step") or "").strip().lower()
    if category in {"barrier_repair"}:
        return "moisturizer"
    if category in {"acne_treatment"}:
        return "treatment"
    if category in {"cleanser", "moisturizer", "sunscreen", "treatment"}:
        return category
    if product.get("is_sunscreen"):
        return "sunscreen"
    if product.get("is_cleanser"):
        return "cleanser"
    if product.get("is_moisturizer"):
        return "moisturizer"
    if product.get("is_active_treatment"):
        return "treatment"
    return category


def _ingredients(product: dict) -> set[str]:
    return _normalized(product.get("ingredient_names", []))


def _affinity_sets(user_affinity: dict[str, dict[str, float]]) -> tuple[set[str], set[str]]:
    problematic = {
        ingredient
        for ingredient, data in (user_affinity or {}).items()
        if float(data.get("confidence", 0) or 0) >= 0.4 and float(data.get("tolerance_score", 0) or 0) <= -0.5
    }
    tolerated = {
        ingredient
        for ingredient, data in (user_affinity or {}).items()
        if float(data.get("confidence", 0) or 0) >= 0.4 and float(data.get("tolerance_score", 0) or 0) >= 0.5
    }
    return problematic, tolerated


def compatibility_component(product: dict) -> int:
    return _clamp(float(product.get("compatibility_score", 0) or 0))


def safety_component(product: dict, skin_profile: SkinProfileInput) -> int:
    ingredients = _ingredients(product)
    score = 100.0
    score -= float(product.get("irritation_risk", 0) or 0) * 0.65
    score -= float(product.get("acne_risk", 0) or 0) * (0.40 if skin_profile.acne_prone else 0.18)
    if skin_profile.sensitive_skin and {"fragrance", "parfum", "perfume"} & ingredients:
        score -= 30
    if skin_profile.barrier_compromised and "alcohol denat" in ingredients:
        score -= 25
    return _clamp(score)


def goal_match_component(product: dict, main_goal: str) -> int:
    ingredients = _ingredients(product)
    weights = GOAL_WEIGHTS.get(main_goal, {})
    score = 35 + sum(weight for ingredient, weight in weights.items() if ingredient in ingredients)
    if main_goal == "hyperpigmentation" and product_category(product) == "sunscreen":
        score += GOAL_WEIGHTS["hyperpigmentation"]["sunscreen"]
    return _clamp(score)


def personalization_component(product: dict, user_affinity: dict[str, dict[str, float]], constraints: Any) -> int:
    ingredients = _ingredients(product)
    historical_problematic, historical_tolerated = _affinity_sets(user_affinity)
    explicit_tolerated = _normalized(_constraint(constraints, "explicit_tolerated_ingredients", []))
    explicit_triggers = _normalized(_constraint(constraints, "explicit_trigger_ingredients", []))
    score = 50
    score += 20 * len(ingredients & explicit_tolerated)
    score += 15 * len(ingredients & historical_tolerated)
    score += 10 if explicit_triggers and not (ingredients & explicit_triggers) else 0
    score -= 30 * len(ingredients & explicit_triggers)
    score -= 25 * len(ingredients & historical_problematic)
    return _clamp(score)


def price_component(product: dict, constraints: Any) -> int:
    target = _constraint(constraints, "price_range")
    if not target:
        return 50
    return 100 if product.get("price_range") == target else 50


def _tie_breaker(product: dict, main_goal: str, constraints: Any) -> int:
    ingredients = _ingredients(product)
    explicit_tolerated = _normalized(_constraint(constraints, "explicit_tolerated_ingredients", []))
    goal_matches = set(GOAL_WEIGHTS.get(main_goal, {})) & ingredients
    return min(3, len(goal_matches) + len(ingredients & explicit_tolerated))


def _passes_hard_filters(product: dict, user_affinity: dict[str, dict[str, float]], constraints: Any) -> bool:
    ingredients = _ingredients(product)
    if not ingredients:
        return False
    if product.get("catalog_status", "active") != "active":
        return False

    preferred = _constraint(constraints, "preferred_category")
    if preferred and product_category(product) != str(preferred).lower():
        return False

    explicit_triggers = _normalized(_constraint(constraints, "explicit_trigger_ingredients", []))
    excluded = _normalized(_constraint(constraints, "exclude_ingredients", [])) | explicit_triggers
    if ingredients & excluded:
        return False

    historical_problematic, _ = _affinity_sets(user_affinity)
    if ingredients & historical_problematic:
        return False

    max_irritation = _constraint(constraints, "max_irritation_risk")
    if max_irritation is not None and float(product.get("irritation_risk", 0) or 0) > float(max_irritation):
        return False
    return True


def _reason_codes(product: dict, breakdown: dict[str, int], main_goal: str, constraints: Any) -> list[str]:
    ingredients = _ingredients(product)
    codes: list[str] = []
    if _constraint(constraints, "preferred_category") and product_category(product) == _constraint(constraints, "preferred_category"):
        codes.append("matches_requested_category")
    if _normalized(_constraint(constraints, "explicit_trigger_ingredients", [])) and not (
        ingredients & _normalized(_constraint(constraints, "explicit_trigger_ingredients", []))
    ):
        codes.append("avoids_explicit_trigger")
    if ingredients & _normalized(_constraint(constraints, "explicit_tolerated_ingredients", [])):
        codes.append("contains_explicit_tolerated_ingredient")
    if breakdown["safety"] >= 75:
        codes.append("low_irritation_risk")
    if _constraint(constraints, "price_range") and product.get("price_range") == _constraint(constraints, "price_range"):
        codes.append("matches_price_preference")
    if goal_match_component(product, main_goal) >= 60:
        codes.append(f"matches_{main_goal}_goal")
    return codes


def generate_human_recommendation_reason(
    product: dict,
    score_breakdown: dict[str, int],
    reason_codes: list[str],
    user_context: dict,
) -> str:
    ingredients = _ingredients(product)
    category = product_category(product) or "produto"
    explicit_tolerated = _normalized(user_context.get("explicit_tolerated_ingredients", []))
    explicit_triggers = _normalized(user_context.get("explicit_trigger_ingredients", []))
    pieces: list[str] = [f"É uma boa opção porque é um {category} alinhado ao que você pediu"]

    if explicit_triggers and not (ingredients & explicit_triggers):
        pieces.append("não contém os gatilhos que você citou")
    tolerated_match = sorted(ingredients & explicit_tolerated)
    if tolerated_match:
        pieces.append(f"tem {tolerated_match[0]}, ingrediente que você relatou tolerar bem")
    acne_oil = [item for item in ["zinc pca", "niacinamide", "salicylic acid"] if item in ingredients]
    if acne_oil:
        pieces.append(f"também traz {', '.join(acne_oil[:2])}, que faz sentido para oleosidade e tendência à acne")
    if score_breakdown["safety"] >= 75:
        pieces.append("ficou com baixo risco de irritação para o perfil informado")
    if "matches_price_preference" in reason_codes:
        pieces.append("está na faixa de preço que você pediu")

    return ". ".join(pieces[:4]) + "."


def rank_recommendations_v3(
    products: list[dict],
    skin_profile: SkinProfileInput,
    main_goal: str,
    user_affinity: dict[str, dict[str, float]] | None = None,
    constraints: Any | None = None,
) -> list[dict]:
    affinity = user_affinity or {}
    ranked: list[dict] = []
    user_context = {
        "explicit_tolerated_ingredients": _constraint(constraints, "explicit_tolerated_ingredients", []),
        "explicit_trigger_ingredients": _constraint(constraints, "explicit_trigger_ingredients", []),
    }
    for product in products:
        if not _passes_hard_filters(product, affinity, constraints):
            continue
        breakdown = {
            "compatibility": compatibility_component(product),
            "safety": safety_component(product, skin_profile),
            "goal_match": goal_match_component(product, main_goal),
            "personalization": personalization_component(product, affinity, constraints),
            "price": price_component(product, constraints),
        }
        final_score = _clamp(
            breakdown["compatibility"] * 0.30
            + breakdown["safety"] * 0.25
            + breakdown["goal_match"] * 0.20
            + breakdown["personalization"] * 0.20
            + breakdown["price"] * 0.05
            + _tie_breaker(product, main_goal, constraints)
        )
        codes = _reason_codes(product, breakdown, main_goal, constraints)
        ranked.append(
            {
                **product,
                "category": product_category(product),
                "final_score": final_score,
                "ranking_score": final_score,
                "score_breakdown": breakdown,
                "reason_codes": codes,
                "reason": generate_human_recommendation_reason(product, breakdown, codes, user_context),
            }
        )
    return sorted(ranked, key=lambda item: (item["final_score"], -item["irritation_risk"]), reverse=True)


def select_best_starting_option(recommendations: list[dict]) -> dict | None:
    if not recommendations:
        return None
    return sorted(
        recommendations,
        key=lambda item: (
            item.get("final_score", 0),
            -float(item.get("irritation_risk", 100) or 100),
            int("contains_explicit_tolerated_ingredient" in item.get("reason_codes", [])),
            int("avoids_explicit_trigger" in item.get("reason_codes", [])),
        ),
        reverse=True,
    )[0]
