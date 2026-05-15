from app.modules.skin_profiles.schemas import SkinProfileInput


GOAL_INGREDIENTS = {
    "acne": {"salicylic acid", "azelaic acid", "benzoyl peroxide", "niacinamide", "zinc pca"},
    "oil_control": {"niacinamide", "zinc pca", "salicylic acid"},
    "barrier": {"ceramide", "panthenol", "glycerin", "hyaluronic acid"},
    "hyperpigmentation": {"niacinamide", "ascorbic acid", "azelaic acid"},
    "texture": {"glycolic acid", "lactic acid", "retinol", "retinal"},
    "anti_aging": {"retinol", "retinal", "ascorbic acid", "niacinamide"},
}


def _normalized(values: list[str]) -> set[str]:
    return {value.strip().lower().removesuffix(".") for value in values if value.strip()}


def final_ranking_score(product_analysis: dict, skin_profile: SkinProfileInput, main_goal: str) -> float:
    compatibility_score = float(product_analysis["compatibility_score"])
    irritation_risk = float(product_analysis["irritation_risk"])
    acne_risk = float(product_analysis["acne_risk"])
    benefit_score = float(product_analysis["benefit_score"])
    ingredient_names = _normalized(product_analysis.get("ingredient_names", []))
    tolerated = _normalized(skin_profile.tolerated_ingredients)
    goal_ingredients = GOAL_INGREDIENTS.get(main_goal, set())

    tolerated_bonus = 5.0 * len(ingredient_names & tolerated)
    goal_bonus = 4.0 * len(ingredient_names & goal_ingredients)
    affinity_penalty = 14.0 * len(product_analysis.get("personal_problematic_ingredients", []))
    affinity_bonus = 6.0 * len(product_analysis.get("personal_well_tolerated_ingredients", []))
    penalty = 0.0

    if irritation_risk > 70:
        penalty += 20.0
    if skin_profile.acne_prone and acne_risk > 55:
        penalty += 12.0

    return (
        compatibility_score * 0.5
        + benefit_score * 0.3
        - irritation_risk * 0.2
        - acne_risk * (0.15 if skin_profile.acne_prone else 0.05)
        + tolerated_bonus
        + goal_bonus
        + affinity_bonus
        - penalty
        - affinity_penalty
    )


def rank_products(products_analysis: list[dict], skin_profile: SkinProfileInput, main_goal: str) -> list[dict]:
    ranked = [
        {
            **analysis,
            "ranking_score": final_ranking_score(analysis, skin_profile, main_goal),
        }
        for analysis in products_analysis
    ]
    return sorted(ranked, key=lambda item: item["ranking_score"], reverse=True)
