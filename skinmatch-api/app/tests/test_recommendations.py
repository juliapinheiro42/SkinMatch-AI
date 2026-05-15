from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.recommendations import service as recommendation_service
from app.modules.recommendations.ranking import rank_products
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
        synonyms=[],
        irritation_risk=irritation_risk,
        acne_risk=acne_risk,
        benefit_acne=benefit_acne,
        benefit_oil_control=benefit_oil_control,
        benefit_barrier=benefit_barrier,
    )


def formula_item(name: str, position: int = 1, band: str = "high") -> dict:
    return {
        "position": position,
        "raw_name": name,
        "normalized_name": name,
        "inci_name": name,
        "unknown": False,
        "concentration_band": band,
    }


def product(name: str, brand: str, ingredients: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        brand=brand,
        formulas=[SimpleNamespace(parsed_formula_snapshot=[formula_item(item, index + 1) for index, item in enumerate(ingredients)])],
    )


def patch_recommendation_dependencies(monkeypatch, products: list[SimpleNamespace]) -> None:
    ingredients = [
        ingredient("salicylic acid", irritation_risk=0.2, acne_risk=0.01, benefit_acne=0.85, benefit_oil_control=0.7),
        ingredient("niacinamide", irritation_risk=0.03, acne_risk=0.01, benefit_acne=0.45, benefit_oil_control=0.55, benefit_barrier=0.35),
        ingredient("glycerin", irritation_risk=0.01, acne_risk=0.01, benefit_barrier=0.7),
        ingredient("fragrance", irritation_risk=0.8, acne_risk=0.08),
        ingredient("benzoyl peroxide", irritation_risk=0.95, acne_risk=0.02, benefit_acne=0.8),
    ]
    monkeypatch.setattr(recommendation_service, "list_products_with_formulas", lambda db, limit=100: products)
    monkeypatch.setattr(recommendation_service, "list_ingredients", lambda db: ingredients)
    monkeypatch.setattr(
        recommendation_service,
        "insights_for_engine",
        lambda db, user_id: {"common_triggers": set(), "well_tolerated_ingredients": set()},
    )


def request_payload(**overrides) -> dict:
    payload = {
        "skin_profile": {
            "skin_type": "oily",
            "sensitive_skin": True,
            "acne_prone": True,
            "barrier_compromised": False,
            "known_triggers": [],
            "tolerated_ingredients": ["niacinamide"],
        },
        "main_goal": "acne",
        "exclude_ingredients": [],
        "limit": 5,
    }
    payload.update(overrides)
    return payload


def test_recommendations_endpoint_returns_ordered_list(monkeypatch) -> None:
    low = product("Hidratante Basico", "Marca A", ["glycerin"])
    high = product("Gel Antiacne X", "Marca Y", ["salicylic acid", "niacinamide"])
    patch_recommendation_dependencies(monkeypatch, [low, high])

    response = TestClient(app).post("/recommendations", json=request_payload())

    assert response.status_code == 200
    body = response.json()
    assert body[0]["product_id"] == str(high.id)
    assert body[0]["name"] == "Gel Antiacne X"


def test_recommendations_exclude_fragrance_from_exclude_ingredients(monkeypatch) -> None:
    blocked = product("Serum Perfumado", "Marca A", ["fragrance", "niacinamide"])
    allowed = product("Gel Sem Perfume", "Marca B", ["salicylic acid"])
    patch_recommendation_dependencies(monkeypatch, [blocked, allowed])

    response = TestClient(app).post(
        "/recommendations",
        json=request_payload(exclude_ingredients=["fragrance"]),
    )

    names = [item["name"] for item in response.json()]
    assert "Serum Perfumado" not in names
    assert "Gel Sem Perfume" in names


def test_recommendations_exclude_known_triggers(monkeypatch) -> None:
    blocked = product("Serum Perfumado", "Marca A", ["fragrance", "niacinamide"])
    allowed = product("Gel Sem Perfume", "Marca B", ["salicylic acid"])
    patch_recommendation_dependencies(monkeypatch, [blocked, allowed])
    payload = request_payload()
    payload["skin_profile"]["known_triggers"] = ["fragrance"]

    response = TestClient(app).post("/recommendations", json=payload)

    names = [item["name"] for item in response.json()]
    assert "Serum Perfumado" not in names
    assert "Gel Sem Perfume" in names


def test_ranking_prioritizes_higher_compatibility() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False)
    ranked = rank_products(
        [
            {"name": "low", "compatibility_score": 60, "benefit_score": 80, "irritation_risk": 10, "acne_risk": 10, "ingredient_names": []},
            {"name": "high", "compatibility_score": 90, "benefit_score": 70, "irritation_risk": 10, "acne_risk": 10, "ingredient_names": []},
        ],
        profile,
        "acne",
    )

    assert ranked[0]["name"] == "high"


def test_ranking_penalizes_high_irritation_risk() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=True, acne_prone=False, barrier_compromised=False)
    ranked = rank_products(
        [
            {"name": "risky", "compatibility_score": 90, "benefit_score": 90, "irritation_risk": 90, "acne_risk": 10, "ingredient_names": []},
            {"name": "calm", "compatibility_score": 82, "benefit_score": 70, "irritation_risk": 10, "acne_risk": 10, "ingredient_names": []},
        ],
        profile,
        "barrier",
    )

    assert ranked[0]["name"] == "calm"


def test_recommendations_response_contains_required_fields(monkeypatch) -> None:
    patch_recommendation_dependencies(monkeypatch, [product("Gel Antiacne X", "Marca Y", ["salicylic acid", "niacinamide"])])

    response = TestClient(app).post("/recommendations", json=request_payload())

    assert response.status_code == 200
    item = response.json()[0]
    assert {
        "product_id",
        "name",
        "brand",
        "compatibility_score",
        "irritation_risk",
        "acne_risk",
        "benefit_score",
        "reason",
        "key_ingredients",
    }.issubset(item)
