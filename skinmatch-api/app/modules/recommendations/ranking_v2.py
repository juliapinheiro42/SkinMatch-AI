from typing import Any

from app.modules.skin_profiles.schemas import SkinProfileInput


GOAL_INGREDIENTS_V2 = {
    "acne": {"salicylic acid", "azelaic acid", "niacinamide", "benzoyl peroxide"},
    "barrier": {"ceramide", "panthenol", "glycerin", "hyaluronic acid"},
    "hyperpigmentation": {"sunscreen", "vitamin c", "ascorbic acid", "niacinamide", "azelaic acid"},
    "oil_control": {"niacinamide", "zinc pca", "salicylic acid"},
}


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> int:
    return round(max(minimum, min(maximum, value)))


def _normalized(values: list[str] | set[str]) -> set[str]:
    return {str(value).strip().lower().removesuffix(".") for value in values if str(value).strip()}


def _constraints_value(constraints: Any, key: str, default: Any = None) -> Any:
    if constraints is None:
        return default
    if isinstance(constraints, dict):
        return constraints.get(key, default)
    return getattr(constraints, key, default)


def _ingredient_names(product: dict) -> set[str]:
    return _normalized(product.get("ingredient_names", []))


def _product_category(product: dict) -> str:
    category = str(product.get("category") or product.get("routine_step") or "").strip().lower()
    if category:
        return category
    if product.get("is_sunscreen"):
        return "sunscreen"
    if product.get("is_cleanser"):
        return "cleanser"
    if product.get("is_moisturizer"):
        return "moisturizer"
    if product.get("is_active_treatment"):
        return "treatment"
    return ""


def _affinity_sets(user_affinity: dict[str, dict[str, float]]) -> tuple[set[str], set[str], bool]:
    if not user_affinity:
        return set(), set(), False
    problematic = {
        ingredient
        for ingredient, data in user_affinity.items()
        if float(data.get("tolerance_score", 0) or 0) <= -0.5
    }
    tolerated = {
        ingredient
        for ingredient, data in user_affinity.items()
        if float(data.get("confidence", 0) or 0) >= 0.4 and float(data.get("tolerance_score", 0) or 0) >= 0.5
    }
    return problematic, tolerated, True


def _matches_goal_ingredient(product: dict, main_goal: str) -> set[str]:
    ingredients = _ingredient_names(product)
    matches = ingredients & GOAL_INGREDIENTS_V2.get(main_goal, set())
    if main_goal == "hyperpigmentation" and (_product_category(product) == "sunscreen" or product.get("is_sunscreen")):
        matches.add("sunscreen")
    return matches


def compatibility_component(product: dict) -> int:
    return _clamp(float(product.get("compatibility_score", 0) or 0))


def goal_match_component(product: dict, main_goal: str) -> int:
    matches = _matches_goal_ingredient(product, main_goal)
    if not GOAL_INGREDIENTS_V2.get(main_goal):
        return 50
    return _clamp(35 + len(matches) * 25)


def safety_component(product: dict, skin_profile: SkinProfileInput) -> int:
    ingredients = _ingredient_names(product)
    score = 100.0
    score -= float(product.get("irritation_risk", 0) or 0) * 0.55
    score -= float(product.get("acne_risk", 0) or 0) * (0.35 if skin_profile.acne_prone else 0.18)
    if skin_profile.sensitive_skin and {"fragrance", "parfum", "perfume"} & ingredients:
        score -= 25
    if skin_profile.barrier_compromised and "alcohol denat" in ingredients:
        score -= 25
    return _clamp(score)


def personalization_component(product: dict, user_affinity: dict[str, dict[str, float]]) -> int:
    problematic, tolerated, has_history = _affinity_sets(user_affinity)
    if not has_history:
        return 50
    ingredients = _ingredient_names(product)
    score = 50 + 18 * len(ingredients & tolerated) - 28 * len(ingredients & problematic)
    return _clamp(score)


def routine_fit_component(product: dict, constraints: Any) -> int:
    score = 50
    category = _product_category(product)
    preferred = _constraints_value(constraints, "preferred_category")
    needed = _constraints_value(constraints, "routine_step_needed")
    usage_periods = _normalized(product.get("usage_periods", []) or [])

    if preferred and category == str(preferred).lower():
        score += 25
    if needed and category == str(needed).lower():
        score += 30
    if (needed == "sunscreen" or preferred == "sunscreen") and (product.get("is_sunscreen") or category == "sunscreen"):
        score += 10
    if "morning" in usage_periods and (product.get("is_sunscreen") or category == "sunscreen"):
        score += 10
    if _constraints_value(constraints, "avoid_active_treatments", False) and product.get("is_active_treatment"):
        score -= 35
    return _clamp(score)


def price_component(product: dict, constraints: Any) -> int:
    target = _constraints_value(constraints, "price_range")
    if not target:
        return 50
    product_price = product.get("price_range")
    if product_price == target:
        return 90
    return 35


def _reason_codes(product: dict, breakdown: dict[str, int], main_goal: str, user_affinity: dict[str, dict[str, float]], constraints: Any) -> list[str]:
    ingredients = _ingredient_names(product)
    problematic, tolerated, _ = _affinity_sets(user_affinity)
    codes: list[str] = []
    if _matches_goal_ingredient(product, main_goal):
        codes.append(f"matches_{main_goal}_goal")
    if breakdown["safety"] >= 75:
        codes.append("low_irritation_risk")
    if not (ingredients & problematic):
        codes.append("avoids_known_triggers")
    if ingredients & tolerated:
        codes.append("contains_well_tolerated_ingredient")
    needed = _constraints_value(constraints, "routine_step_needed")
    preferred = _constraints_value(constraints, "preferred_category")
    if needed and _product_category(product) == str(needed).lower():
        codes.append("fits_missing_routine_step")
    if preferred and _product_category(product) == str(preferred).lower():
        codes.append("matches_preferred_category")
    if _constraints_value(constraints, "price_range") and product.get("price_range") == _constraints_value(constraints, "price_range"):
        codes.append("matches_price_range")
    return codes


def generate_recommendation_reason(score_breakdown: dict[str, int], reason_codes: list[str]) -> str:
    parts: list[str] = []
    if any(code.startswith("matches_") and code.endswith("_goal") for code in reason_codes):
        parts.append("combina com seu objetivo principal")
    if "low_irritation_risk" in reason_codes:
        parts.append("tem baixo risco de irritacao")
    if "avoids_known_triggers" in reason_codes:
        parts.append("evita seus possiveis gatilhos")
    if "contains_well_tolerated_ingredient" in reason_codes:
        parts.append("inclui ingrediente bem tolerado no seu historico")
    if "fits_missing_routine_step" in reason_codes:
        parts.append("preenche uma etapa que faltava na rotina")
    if "matches_price_range" in reason_codes:
        parts.append("esta dentro da faixa de preco desejada")

    if not parts:
        strongest = max(score_breakdown, key=score_breakdown.get)
        labels = {
            "compatibility": "boa compatibilidade geral",
            "goal_match": "boa relacao com o objetivo",
            "safety": "perfil de seguranca melhor",
            "personalization": "melhor ajuste ao seu historico",
            "routine_fit": "bom encaixe na rotina",
            "price": "bom encaixe de preco",
        }
        parts.append(labels.get(strongest, "bom equilibrio geral"))

    return "Boa opcao porque " + ", ".join(parts[:3]) + "."


def _passes_hard_filters(product: dict, user_affinity: dict[str, dict[str, float]], constraints: Any) -> bool:
    ingredients = _ingredient_names(product)
    exclude = _normalized(product.get("exclude_ingredients", [])) | _normalized(_constraints_value(constraints, "exclude_ingredients", []))
    high_confidence_problematic = {
        ingredient
        for ingredient, data in user_affinity.items()
        if float(data.get("confidence", 0) or 0) >= 0.4 and float(data.get("tolerance_score", 0) or 0) <= -0.5
    }
    max_irritation = _constraints_value(constraints, "max_irritation_risk", None)

    if not ingredients:
        return False
    if product.get("catalog_status", "active") != "active":
        return False
    if ingredients & exclude:
        return False
    if ingredients & high_confidence_problematic:
        return False
    if float(product.get("irritation_risk", 0) or 0) > 90:
        return False
    if max_irritation is not None and float(product.get("irritation_risk", 0) or 0) > float(max_irritation):
        return False
    if _constraints_value(constraints, "avoid_active_treatments", False) and product.get("is_active_treatment"):
        return False
    return True


def rank_recommendations_v2(
    products: list[dict],
    skin_profile: SkinProfileInput,
    main_goal: str,
    user_affinity: dict[str, dict[str, float]] | None = None,
    constraints: Any | None = None,
) -> list[dict]:
    affinity = user_affinity or {}
    ranked: list[dict] = []

    for product in products:
        if not _passes_hard_filters(product, affinity, constraints):
            continue

        breakdown = {
            "compatibility": compatibility_component(product),
            "goal_match": goal_match_component(product, main_goal),
            "safety": safety_component(product, skin_profile),
            "personalization": personalization_component(product, affinity),
            "routine_fit": routine_fit_component(product, constraints),
            "price": price_component(product, constraints),
        }
        final_score = _clamp(
            breakdown["compatibility"] * 0.35
            + breakdown["goal_match"] * 0.20
            + breakdown["safety"] * 0.20
            + breakdown["personalization"] * 0.15
            + breakdown["routine_fit"] * 0.05
            + breakdown["price"] * 0.05
        )
        reason_codes = _reason_codes(product, breakdown, main_goal, affinity, constraints)
        ranked.append(
            {
                **product,
                "final_score": final_score,
                "ranking_score": final_score,
                "score_breakdown": breakdown,
                "reason_codes": reason_codes,
                "reason": generate_recommendation_reason(breakdown, reason_codes),
            }
        )

    return sorted(ranked, key=lambda item: item["final_score"], reverse=True)
