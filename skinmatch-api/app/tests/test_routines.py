from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.routines import service as routine_service


def product(name: str, routine_type: str, ingredients: list[str], score: int = 80, risk: int = 10) -> dict:
    return {
        "product_id": uuid4(),
        "name": name,
        "brand": "Marca",
        "compatibility_score": score,
        "irritation_risk": risk,
        "acne_risk": 10,
        "benefit_score": 70,
        "ranking_score": score - risk,
        "ingredient_names": ingredients,
        "positive_ingredients": ingredients,
        "routine_type": routine_type,
    }


def payload(**overrides) -> dict:
    data = {
        "skin_profile": {
            "skin_type": "oily",
            "sensitive_skin": False,
            "acne_prone": True,
            "barrier_compromised": False,
            "known_triggers": [],
            "tolerated_ingredients": ["niacinamide"],
        },
        "main_goal": "acne",
        "constraints": {"avoid_ingredients": ["fragrance"], "max_steps": 5},
    }
    data.update(overrides)
    return data


def patch_products(monkeypatch, products: list[dict]) -> None:
    monkeypatch.setattr(routine_service, "recommendation_analyses", lambda db, request: products)


def test_routine_contains_sunscreen_in_morning(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Gel de limpeza", "cleanser", []),
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
            product("Niacinamide Serum", "treatment", ["niacinamide"]),
        ],
    )

    response = TestClient(app).post("/routines/generate", json=payload())

    assert response.status_code == 200
    assert any(step["type"] == "sunscreen" for step in response.json()["morning_routine"])


def test_routine_respects_max_steps(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Gel de limpeza", "cleanser", []),
            product("Toner", "toner", []),
            product("Serum", "treatment", ["niacinamide"]),
            product("Creme", "moisturizer", ["glycerin"]),
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
        ],
    )

    response = TestClient(app).post("/routines/generate", json=payload(constraints={"avoid_ingredients": [], "max_steps": 3}))
    body = response.json()

    assert len(body["morning_routine"]) <= 3
    assert len(body["night_routine"]) <= 3


def test_routine_does_not_mix_retinol_and_acid(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Retinol", "treatment", ["retinol"], score=92),
            product("AHA", "treatment", ["glycolic acid"], score=88),
            product("Gel de limpeza", "cleanser", []),
            product("Creme", "moisturizer", ["glycerin"]),
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
        ],
    )

    response = TestClient(app).post("/routines/generate", json=payload())
    for routine_name in ("morning_routine", "night_routine"):
        ingredients = " ".join(step["product"]["name"].lower() for step in response.json()[routine_name])
        assert not ("retinol" in ingredients and "aha" in ingredients)


def test_routine_changes_when_sensitive_skin(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Benzoyl", "treatment", ["benzoyl peroxide"], score=95, risk=80),
            product("Niacinamide", "treatment", ["niacinamide"], score=84, risk=5),
            product("Gel de limpeza", "cleanser", []),
            product("Creme", "moisturizer", ["glycerin"]),
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
        ],
    )
    sensitive_payload = payload()
    sensitive_payload["skin_profile"]["sensitive_skin"] = True

    response = TestClient(app).post("/routines/generate", json=sensitive_payload)
    names = [step["product"]["name"] for step in response.json()["night_routine"]]

    assert "Niacinamide" in names


def test_routine_changes_when_goal_is_acne(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Shea Cream", "moisturizer", ["shea butter"], score=95),
            product("Salicylic Serum", "treatment", ["salicylic acid"], score=86),
            product("Gel de limpeza", "cleanser", []),
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
        ],
    )

    response = TestClient(app).post("/routines/generate", json=payload())
    names = [step["product"]["name"] for step in response.json()["night_routine"]]

    assert "Shea Cream" not in names
    assert "Salicylic Serum" in names


def test_routine_products_do_not_repeat(monkeypatch) -> None:
    repeated = product("Niacinamide", "treatment", ["niacinamide"])
    patch_products(monkeypatch, [repeated, product("Gel de limpeza", "cleanser", []), product("Protetor SPF", "sunscreen", ["zinc oxide"])])

    response = TestClient(app).post("/routines/generate", json=payload())
    ids = [step["product"]["id"] for routine in ("morning_routine", "night_routine") for step in response.json()[routine]]

    assert len(ids) == len(set(ids))


def test_routine_step_order_is_correct(monkeypatch) -> None:
    patch_products(
        monkeypatch,
        [
            product("Protetor SPF", "sunscreen", ["zinc oxide"]),
            product("Creme", "moisturizer", ["glycerin"]),
            product("Serum", "treatment", ["niacinamide"]),
            product("Gel de limpeza", "cleanser", []),
        ],
    )

    response = TestClient(app).post("/routines/generate", json=payload())
    morning_types = [step["type"] for step in response.json()["morning_routine"]]

    assert morning_types == sorted(morning_types, key=["cleanser", "treatment", "moisturizer", "sunscreen"].index)
