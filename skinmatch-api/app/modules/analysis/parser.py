from typing import Any


def normalize_ingredient_name(value: str) -> str:
    return value.strip().lower().removesuffix(".")


def concentration_band(position: int) -> str:
    if position <= 3:
        return "high"
    if position <= 8:
        return "medium"
    return "low"


def _ingredient_lookup(ingredients_db: list[Any]) -> dict[str, Any]:
    lookup: dict[str, Any] = {}
    for ingredient in ingredients_db:
        inci_name = normalize_ingredient_name(ingredient.inci_name)
        lookup[inci_name] = ingredient
        for synonym in ingredient.synonyms:
            lookup[normalize_ingredient_name(synonym)] = ingredient
    return lookup


def parse_formula(raw_ingredient_list: str, ingredients_db: list[Any]) -> list[dict]:
    lookup = _ingredient_lookup(ingredients_db)
    parsed: list[dict] = []

    for index, raw_name in enumerate(raw_ingredient_list.split(","), start=1):
        normalized_name = normalize_ingredient_name(raw_name)
        if not normalized_name:
            continue

        ingredient = lookup.get(normalized_name)
        canonical_name = ingredient.inci_name if ingredient else normalized_name

        parsed.append(
            {
                "position": len(parsed) + 1,
                "raw_name": raw_name.strip(),
                "normalized_name": normalized_name,
                "inci_name": canonical_name,
                "unknown": ingredient is None,
                "concentration_band": concentration_band(len(parsed) + 1),
                "ingredient": ingredient,
            }
        )

    return parsed
