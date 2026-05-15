from types import SimpleNamespace
from uuid import uuid4

from app.modules.agent.response_templates import render_analyze_product
from app.modules.analysis.engine import analyze_formula
from app.modules.personalization import service as personalization_service
from app.modules.recommendations.ranking import rank_products
from app.modules.routines.service import select_best_products_for_routine
from app.modules.skin_profiles.schemas import SkinProfileInput


def ingredient(
    inci_name: str,
    irritation_risk: float = 0.0,
    acne_risk: float = 0.0,
    benefit_acne: float = 0.0,
    benefit_oil_control: float = 0.0,
    benefit_barrier: float = 0.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        inci_name=inci_name,
        irritation_risk=irritation_risk,
        acne_risk=acne_risk,
        benefit_acne=benefit_acne,
        benefit_oil_control=benefit_oil_control,
        benefit_barrier=benefit_barrier,
    )


def parsed(item: SimpleNamespace, band: str = "high") -> dict:
    return {
        "position": 1,
        "raw_name": item.inci_name,
        "normalized_name": item.inci_name,
        "inci_name": item.inci_name,
        "unknown": False,
        "concentration_band": band,
        "ingredient": item,
    }


def feedback(**overrides) -> SimpleNamespace:
    data = {
        "irritation_level": 0,
        "acne_level": 0,
        "satisfaction_level": 3,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def product(name: str, routine_type: str, ingredients: list[str], score: int = 80) -> dict:
    return {
        "product_id": uuid4(),
        "name": name,
        "brand": "Marca",
        "routine_type": routine_type,
        "compatibility_score": score,
        "irritation_risk": 10,
        "acne_risk": 10,
        "benefit_score": 70,
        "ranking_score": score,
        "ingredient_names": ingredients,
    }


def test_feedback_high_irritation_reduces_tolerance_score(monkeypatch) -> None:
    saved = {}
    record = SimpleNamespace(parsed_formula_snapshot=[{"inci_name": "fragrance"}])
    monkeypatch.setattr(personalization_service, "get_analysis_record", lambda db, user_id, analysis_id: record)
    monkeypatch.setattr(personalization_service, "get_affinity_by_ingredient", lambda db, user_id, ingredient_name: None)
    monkeypatch.setattr(personalization_service, "upsert_affinity", lambda db, affinity: saved.setdefault("item", affinity))

    personalization_service.update_affinity_from_feedback(
        SimpleNamespace(),
        uuid4(),
        uuid4(),
        feedback(irritation_level=4, satisfaction_level=1),
    )

    assert saved["item"].tolerance_score < 0
    assert saved["item"].irritation_count == 1


def test_feedback_positive_increases_tolerance_score(monkeypatch) -> None:
    saved = {}
    record = SimpleNamespace(parsed_formula_snapshot=[{"inci_name": "niacinamide"}])
    monkeypatch.setattr(personalization_service, "get_analysis_record", lambda db, user_id, analysis_id: record)
    monkeypatch.setattr(personalization_service, "get_affinity_by_ingredient", lambda db, user_id, ingredient_name: None)
    monkeypatch.setattr(personalization_service, "upsert_affinity", lambda db, affinity: saved.setdefault("item", affinity))

    personalization_service.update_affinity_from_feedback(
        SimpleNamespace(),
        uuid4(),
        uuid4(),
        feedback(irritation_level=0, satisfaction_level=5),
    )

    assert saved["item"].tolerance_score > 0
    assert saved["item"].positive_count == 1


def test_confidence_increases_with_occurrences(monkeypatch) -> None:
    affinity = None
    record = SimpleNamespace(parsed_formula_snapshot=[{"inci_name": "fragrance"}])

    def fake_get_affinity(db, user_id, ingredient_name):
        return affinity

    def fake_upsert(db, item):
        nonlocal affinity
        affinity = item
        return item

    monkeypatch.setattr(personalization_service, "get_analysis_record", lambda db, user_id, analysis_id: record)
    monkeypatch.setattr(personalization_service, "get_affinity_by_ingredient", fake_get_affinity)
    monkeypatch.setattr(personalization_service, "upsert_affinity", fake_upsert)

    for _ in range(4):
        personalization_service.update_affinity_from_feedback(
            SimpleNamespace(),
            uuid4(),
            uuid4(),
            feedback(irritation_level=4, satisfaction_level=1),
        )

    assert affinity.confidence >= 0.9
    assert affinity.irritation_count == 4


def test_engine_applies_rule_010_for_problematic_affinity() -> None:
    fragrance = ingredient("fragrance", irritation_risk=0.1, acne_risk=0.05)
    result = analyze_formula(
        [parsed(fragrance)],
        SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False),
        personal_insights={"ingredient_affinity": {"fragrance": {"tolerance_score": -0.7, "confidence": 0.8}}},
    )

    assert "RULE_010" in result["applied_rules"]
    assert "fragrance" in result["warning_ingredients"]


def test_engine_applies_rule_011_for_tolerated_affinity() -> None:
    niacinamide = ingredient("niacinamide", irritation_risk=0.2, benefit_acne=0.2)
    result = analyze_formula(
        [parsed(niacinamide)],
        SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False),
        personal_insights={"ingredient_affinity": {"niacinamide": {"tolerance_score": 0.7, "confidence": 0.8}}},
    )

    assert "RULE_011" in result["applied_rules"]
    assert "niacinamide" in result["positive_ingredients"]


def test_recommendations_penalize_problematic_ingredients() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False)
    ranked = rank_products(
        [
            {
                "name": "problematic",
                "compatibility_score": 90,
                "benefit_score": 80,
                "irritation_risk": 10,
                "acne_risk": 10,
                "ingredient_names": ["fragrance"],
                "personal_problematic_ingredients": ["fragrance"],
            },
            {
                "name": "calm",
                "compatibility_score": 84,
                "benefit_score": 70,
                "irritation_risk": 10,
                "acne_risk": 10,
                "ingredient_names": ["glycerin"],
            },
        ],
        profile,
        "barrier",
    )

    assert ranked[0]["name"] == "calm"


def test_routine_avoids_problematic_treatment() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False)
    morning, night = select_best_products_for_routine(
        [
            product("Serum Perfumado", "treatment", ["fragrance"], score=96),
            product("Niacinamide", "treatment", ["niacinamide"], score=84),
            product("Gel", "cleanser", []),
            product("Creme", "moisturizer", ["glycerin"]),
            product("SPF", "sunscreen", ["zinc oxide"]),
        ],
        profile,
        "acne",
        5,
        {"fragrance": {"tolerance_score": -0.8, "confidence": 0.8}},
    )

    selected_names = {item["name"] for item in morning + night}
    assert "Serum Perfumado" not in selected_names
    assert "Niacinamide" in selected_names


def test_agent_mentions_affinity_history_when_relevant() -> None:
    answer = render_analyze_product(
        {
            "verdict": "caution",
            "compatibility_score": 62,
            "positive_ingredients": ["niacinamide"],
            "warning_ingredients": ["fragrance"],
        },
        {
            "known_triggers": ["fragrance"],
            "ingredient_affinity": {
                "problematic": [
                    {
                        "ingredient_name": "fragrance",
                        "tolerance_score": -0.8,
                        "confidence": 0.9,
                    }
                ]
            },
        },
    )

    assert "Afinidade aprendida: fragrance" in answer
