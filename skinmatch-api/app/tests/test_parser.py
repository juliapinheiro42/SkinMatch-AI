from types import SimpleNamespace

from app.modules.analysis.parser import parse_formula


def ingredient(inci_name: str, synonyms: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(inci_name=inci_name, synonyms=synonyms or [])


def test_parser_normalizes_synonyms_positions_and_bands() -> None:
    ingredients = [
        ingredient("fragrance", ["parfum", "perfume"]),
        ingredient("salicylic acid", ["bha"]),
        ingredient("glycerin"),
    ]

    parsed = parse_formula(
        " Water, Parfum., BHA, Glycerin, Unknown One, Unknown Two, Unknown Three, Unknown Four, Unknown Five ",
        ingredients,
    )

    assert parsed[1]["normalized_name"] == "parfum"
    assert parsed[1]["inci_name"] == "fragrance"
    assert parsed[1]["position"] == 2
    assert parsed[2]["inci_name"] == "salicylic acid"
    assert parsed[0]["concentration_band"] == "high"
    assert parsed[3]["concentration_band"] == "medium"
    assert parsed[8]["concentration_band"] == "low"
    assert parsed[4]["unknown"] is True
