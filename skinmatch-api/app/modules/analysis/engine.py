from app.modules.skin_profiles.schemas import SkinProfileInput


CONCENTRATION_WEIGHTS = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _normalize_names(values: list[str]) -> set[str]:
    return {value.strip().lower().removesuffix(".") for value in values}


def _personal_names(personal_insights: dict | None, key: str) -> set[str]:
    if not personal_insights:
        return set()
    values = personal_insights.get(key, set())
    return _normalize_names(list(values))


def _affinity_for(personal_insights: dict | None, ingredient_name: str) -> dict:
    if not personal_insights:
        return {}
    affinity = personal_insights.get("ingredient_affinity") or {}
    return affinity.get(ingredient_name.strip().lower().removesuffix("."), {})


def calculate_base_formula(parsed_ingredients: list[dict]) -> dict:
    irritation_risk = 0.0
    acne_risk = 0.0
    benefit_score = 0.0
    barrier_support = 0.0

    for parsed in parsed_ingredients:
        if parsed["unknown"]:
            continue

        ingredient = parsed["ingredient"]
        weight = CONCENTRATION_WEIGHTS[parsed["concentration_band"]]
        irritation_risk += ingredient.irritation_risk * weight
        acne_risk += ingredient.acne_risk * weight
        benefit_score += (
            ingredient.benefit_acne * 0.55
            + ingredient.benefit_oil_control * 0.55
            + ingredient.benefit_barrier * 0.55
        ) * weight
        barrier_support += ingredient.benefit_barrier * weight

    return {
        "base_irritation_risk": round(_clamp(irritation_risk, 0, 1), 3),
        "base_acne_risk": round(_clamp(acne_risk, 0, 1), 3),
        "base_benefit_score": round(_clamp(benefit_score, 0, 1), 3),
        "base_barrier_support": round(_clamp(barrier_support, 0, 1), 3),
    }


def analyze_formula(
    parsed_ingredients: list[dict],
    skin_profile: SkinProfileInput,
    personal_insights: dict | None = None,
    base_cache: dict | None = None,
) -> dict:
    base = base_cache or calculate_base_formula(parsed_ingredients)
    irritation_risk = float(base.get("base_irritation_risk", 0.0))
    acne_risk = float(base.get("base_acne_risk", 0.0))
    benefit_score = float(base.get("base_benefit_score", 0.0))
    barrier_support = float(base.get("base_barrier_support", 0.0))
    applied_rules: list[str] = []
    positive_ingredients: set[str] = set()
    warning_ingredients: set[str] = set()

    known_triggers = _normalize_names(skin_profile.known_triggers)
    tolerated_ingredients = _normalize_names(skin_profile.tolerated_ingredients)
    personal_triggers = _personal_names(personal_insights, "common_triggers")
    personally_tolerated = _personal_names(personal_insights, "well_tolerated_ingredients")

    for parsed in parsed_ingredients:
        if parsed["unknown"]:
            continue

        ingredient = parsed["ingredient"]
        name = ingredient.inci_name.strip().lower().removesuffix(".")
        weight = CONCENTRATION_WEIGHTS[parsed["concentration_band"]]
        tolerated = name in tolerated_ingredients
        risk_multiplier = 0.5 if tolerated else 1.0

        if tolerated:
            irritation_risk -= ingredient.irritation_risk * weight * 0.5
            acne_risk -= ingredient.acne_risk * weight * 0.5

        ingredient_benefit = (
            ingredient.benefit_acne * (1.0 if skin_profile.acne_prone else 0.4)
            + ingredient.benefit_oil_control * (1.0 if skin_profile.skin_type == "oily" else 0.35)
            + ingredient.benefit_barrier * (1.0 if skin_profile.barrier_compromised else 0.55)
        ) * weight
        baseline_benefit = (
            ingredient.benefit_acne * 0.55
            + ingredient.benefit_oil_control * 0.55
            + ingredient.benefit_barrier * 0.55
        ) * weight
        benefit_score += ingredient_benefit - baseline_benefit

        if ingredient_benefit >= 0.35:
            positive_ingredients.add(name)
        if ingredient.irritation_risk * weight >= 0.35 or ingredient.acne_risk * weight >= 0.35:
            warning_ingredients.add(name)

        if tolerated and (ingredient.irritation_risk > 0 or ingredient.acne_risk > 0):
            applied_rules.append("RULE_006")

        if name in known_triggers:
            irritation_risk += 0.45 * weight
            warning_ingredients.add(name)
            applied_rules.append("RULE_005")

        if name in personal_triggers:
            irritation_risk += 0.20 * weight
            warning_ingredients.add(name)
            applied_rules.append("RULE_008")

        if name in personally_tolerated:
            irritation_risk -= 0.10 * weight
            benefit_score += 0.05 * weight
            positive_ingredients.add(name)
            applied_rules.append("RULE_009")

        affinity = _affinity_for(personal_insights, name)
        tolerance_score = float(affinity.get("tolerance_score", 0.0) or 0.0)
        confidence = float(affinity.get("confidence", 0.0) or 0.0)

        if confidence < 0.4 and abs(tolerance_score) >= 0.3:
            applied_rules.append("RULE_012")
        elif tolerance_score <= -0.5:
            irritation_risk += 0.25 * weight
            acne_risk += 0.15 * weight
            warning_ingredients.add(name)
            applied_rules.append("RULE_010")
        elif tolerance_score >= 0.5:
            irritation_risk -= 0.10 * weight
            benefit_score += 0.10 * weight
            positive_ingredients.add(name)
            applied_rules.append("RULE_011")

    ingredient_names = {parsed["inci_name"] for parsed in parsed_ingredients if not parsed["unknown"]}

    if skin_profile.sensitive_skin and "fragrance" in ingredient_names:
        irritation_risk += 0.35
        warning_ingredients.add("fragrance")
        applied_rules.append("RULE_001")

    if skin_profile.barrier_compromised and "alcohol denat" in ingredient_names:
        irritation_risk += 0.35
        barrier_support -= 0.2
        warning_ingredients.add("alcohol denat")
        applied_rules.append("RULE_002")

    if skin_profile.acne_prone and "salicylic acid" in ingredient_names:
        acne_risk -= 0.2
        benefit_score += 0.45
        positive_ingredients.add("salicylic acid")
        applied_rules.append("RULE_003")

    if {"retinol", "glycolic acid"}.issubset(ingredient_names):
        irritation_risk += 0.3
        warning_ingredients.update({"retinol", "glycolic acid"})
        applied_rules.append("RULE_004")

    barrier_boosters = {"ceramide", "panthenol", "glycerin"} & ingredient_names
    if barrier_boosters:
        barrier_support += 0.25 * len(barrier_boosters)
        benefit_score += 0.2 * len(barrier_boosters)
        positive_ingredients.update(barrier_boosters)
        applied_rules.append("RULE_007")

    irritation_risk = round(_clamp(irritation_risk, 0, 1), 3)
    acne_risk = round(_clamp(acne_risk, 0, 1), 3)
    benefit_score = round(_clamp(benefit_score, 0, 1), 3)
    barrier_support = round(_clamp(barrier_support, 0, 1), 3)

    final_score = 72 + (benefit_score * 24) + (barrier_support * 12) - (irritation_risk * 38) - (acne_risk * 24)
    compatibility_score = int(round(_clamp(final_score, 0, 100)))

    if compatibility_score >= 80:
        verdict = "good_match"
        recommendation = "Formula appears compatible with this profile. Introduce gradually and monitor skin response."
    elif compatibility_score >= 60:
        verdict = "caution"
        recommendation = "Formula has useful ingredients but also some cautions. Patch testing is recommended."
    else:
        verdict = "high_risk"
        recommendation = "Formula may not be ideal for this profile due to elevated risk signals."

    unknown_ingredients = [parsed["inci_name"] for parsed in parsed_ingredients if parsed["unknown"]]

    return {
        "compatibility_score": compatibility_score,
        "verdict": verdict,
        "irritation_risk": irritation_risk,
        "acne_risk": acne_risk,
        "benefit_score": benefit_score,
        "barrier_support": barrier_support,
        "applied_rules": sorted(set(applied_rules)),
        "positive_ingredients": sorted(positive_ingredients),
        "warning_ingredients": sorted(warning_ingredients),
        "unknown_ingredients": unknown_ingredients,
        "recommendation": recommendation,
        "disclaimer": "This deterministic analysis is informational and does not replace medical advice.",
    }
