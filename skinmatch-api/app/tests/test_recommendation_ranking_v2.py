from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.agent import service as agent_service
from app.modules.recommendations.ranking_v2 import rank_recommendations_v2
from app.modules.skin_profiles.schemas import SkinProfileInput


def profile(**overrides) -> SkinProfileInput:
    data = {
        "skin_type": "oily",
        "sensitive_skin": True,
        "acne_prone": True,
        "barrier_compromised": False,
        "known_triggers": [],
        "tolerated_ingredients": [],
    }
    data.update(overrides)
    return SkinProfileInput(**data)


def product(name: str, ingredients: list[str], **overrides) -> dict:
    data = {
        "product_id": uuid4(),
        "name": name,
        "brand": "Marca",
        "compatibility_score": 80,
        "irritation_risk": 20,
        "acne_risk": 10,
        "benefit_score": 70,
        "ingredient_names": ingredients,
        "category": "treatment",
        "routine_step": "treatment",
        "price_range": "mid",
        "catalog_status": "active",
        "is_active_treatment": True,
        "is_sunscreen": False,
        "is_moisturizer": False,
        "is_cleanser": False,
    }
    data.update(overrides)
    return data


def test_hard_filter_removes_fragrance_when_excluded() -> None:
    ranked = rank_recommendations_v2(
        [
            product("Perfumado", ["niacinamide", "fragrance"]),
            product("Sem perfume", ["niacinamide"]),
        ],
        profile(),
        "acne",
        {},
        {"exclude_ingredients": ["fragrance"]},
    )

    assert [item["name"] for item in ranked] == ["Sem perfume"]


def test_goal_aligned_product_gets_higher_score() -> None:
    ranked = rank_recommendations_v2(
        [
            product("Basico", ["glycerin"], compatibility_score=82),
            product("Acne Fit", ["salicylic acid", "niacinamide"], compatibility_score=82),
        ],
        profile(),
        "acne",
        {},
        {},
    )

    assert ranked[0]["name"] == "Acne Fit"
    assert ranked[0]["score_breakdown"]["goal_match"] > ranked[1]["score_breakdown"]["goal_match"]


def test_problematic_ingredient_reduces_personalization_component() -> None:
    ranked = rank_recommendations_v2(
        [
            product("Problematico", ["fragrance"]),
            product("Neutro", ["glycerin"]),
        ],
        profile(),
        "barrier",
        {"fragrance": {"tolerance_score": -0.8, "confidence": 0.3}},
        {},
    )

    item = next(product for product in ranked if product["name"] == "Problematico")
    assert item["score_breakdown"]["personalization"] < 50


def test_well_tolerated_ingredient_increases_personalization_component() -> None:
    ranked = rank_recommendations_v2(
        [product("Tolerado", ["niacinamide"])],
        profile(),
        "acne",
        {"niacinamide": {"tolerance_score": 0.8, "confidence": 0.9}},
        {},
    )

    assert ranked[0]["score_breakdown"]["personalization"] > 50


def test_low_risk_product_rises_in_ranking() -> None:
    ranked = rank_recommendations_v2(
        [
            product("Arriscado", ["niacinamide"], compatibility_score=86, irritation_risk=85),
            product("Calmo", ["niacinamide"], compatibility_score=82, irritation_risk=8),
        ],
        profile(),
        "acne",
        {},
        {},
    )

    assert ranked[0]["name"] == "Calmo"


def test_reason_codes_are_returned() -> None:
    ranked = rank_recommendations_v2(
        [product("Acne Fit", ["salicylic acid", "niacinamide"], price_range="low")],
        profile(),
        "acne",
        {"niacinamide": {"tolerance_score": 0.8, "confidence": 0.9}},
        {"price_range": "low"},
    )

    assert "matches_acne_goal" in ranked[0]["reason_codes"]
    assert "contains_well_tolerated_ingredient" in ranked[0]["reason_codes"]
    assert "matches_price_range" in ranked[0]["reason_codes"]
    assert ranked[0]["reason"]


def test_price_constraints_influence_ranking() -> None:
    ranked = rank_recommendations_v2(
        [
            product("Caro", ["niacinamide"], price_range="high"),
            product("Barato", ["niacinamide"], price_range="low"),
        ],
        profile(),
        "acne",
        {},
        {"price_range": "low"},
    )

    assert ranked[0]["name"] == "Barato"
    assert ranked[0]["score_breakdown"]["price"] > ranked[1]["score_breakdown"]["price"]


def test_agent_turns_cheap_fragrance_free_message_into_constraints(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        agent_service,
        "build_agent_context",
        lambda db, user_id, skin_profile=None: {
            "skin_profile": skin_profile.model_dump(mode="json") if skin_profile else None,
            "personal_insights": {},
            "recent_analysis": [],
            "recent_feedbacks": [],
            "current_routine": None,
            "known_triggers": [],
            "tolerated_ingredients": [],
            "recent_reactions": [],
            "recent_products_used": [],
            "user_goals": [],
            "conversation_summary": {},
            "context_status": "available",
        },
    )
    monkeypatch.setattr(agent_service, "save_message", lambda *args, **kwargs: SimpleNamespace(id=uuid4()))

    def fake_recommend(*args, **kwargs):
        captured.update(kwargs)
        return [
            {
                "product_id": str(uuid4()),
                "name": "Gel barato",
                "brand": "Marca",
                "compatibility_score": 80,
                "irritation_risk": 10,
                "acne_risk": 10,
                "benefit_score": 70,
                "final_score": 84,
                "score_breakdown": {
                    "compatibility": 80,
                    "goal_match": 80,
                    "safety": 90,
                    "personalization": 50,
                    "routine_fit": 50,
                    "price": 90,
                },
                "reason_codes": ["matches_price_range", "avoids_known_triggers"],
                "reason": "Boa opcao.",
                "key_ingredients": ["niacinamide"],
            }
        ]

    monkeypatch.setattr(agent_service, "recommend_products_tool", fake_recommend)

    response = TestClient(app).post(
        "/agent/chat",
        json={
            "message": "quero opcao barata sem fragrancia",
            "context": {
                "skin_profile": profile().model_dump(mode="json"),
                "main_goal": "acne",
            },
        },
    )

    assert response.status_code == 200
    assert captured["constraints"]["price_range"] == "low"
    assert "fragrance" in captured["constraints"]["exclude_ingredients"]
