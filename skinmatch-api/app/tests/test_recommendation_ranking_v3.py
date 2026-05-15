from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.agent import service as agent_service
from app.modules.agent.planner import extract_explicit_user_preferences, plan_agent_response
from app.modules.agent.schemas import AgentChatRequest, AgentIntent
from app.modules.recommendations.ranking_v3 import rank_recommendations_v3, select_best_starting_option
from app.modules.skin_profiles.schemas import SkinProfileInput


def profile() -> SkinProfileInput:
    return SkinProfileInput(
        skin_type="oily",
        sensitive_skin=True,
        acne_prone=True,
        barrier_compromised=False,
        known_triggers=[],
        tolerated_ingredients=[],
    )


def product(name: str, category: str, ingredients: list[str], **overrides) -> dict:
    data = {
        "product_id": uuid4(),
        "name": name,
        "brand": "Marca",
        "category": category,
        "routine_step": category,
        "price_range": "mid",
        "catalog_status": "active",
        "compatibility_score": 80,
        "irritation_risk": 15,
        "acne_risk": 8,
        "benefit_score": 70,
        "ingredient_names": ingredients,
        "is_moisturizer": category == "moisturizer",
        "is_sunscreen": category == "sunscreen",
        "is_cleanser": category == "cleanser",
        "is_active_treatment": category == "treatment",
    }
    data.update(overrides)
    return data


def test_hydrating_cheap_fragrance_free_filters_category_and_price() -> None:
    request = AgentChatRequest(message="quero hidratante barato sem fragrancia")
    plan = plan_agent_response(request, {"context_status": "available"})
    constraints = plan.recommendation_payload["constraints"]

    ranked = rank_recommendations_v3(
        [
            product("Creme leve", "moisturizer", ["niacinamide", "glycerin"], price_range="low"),
            product("Protetor leve", "sunscreen", ["niacinamide"], price_range="low"),
            product("Creme perfumado", "moisturizer", ["fragrance", "glycerin"], price_range="low"),
        ],
        profile(),
        plan.recommendation_payload["main_goal"],
        {},
        {**constraints, "exclude_ingredients": plan.recommendation_payload["exclude_ingredients"]},
    )

    assert constraints["preferred_category"] == "moisturizer"
    assert constraints["price_range"] == "low"
    assert "fragrance" in plan.recommendation_payload["exclude_ingredients"]
    assert [item["name"] for item in ranked] == ["Creme leve"]


def test_niacinamide_worked_boosts_personalization() -> None:
    explicit = extract_explicit_user_preferences("minha pele ficou otima com niacinamide")
    ranked = rank_recommendations_v3(
        [
            product("Com niacinamide", "moisturizer", ["niacinamide", "glycerin"]),
            product("Sem niacinamide", "moisturizer", ["glycerin"]),
        ],
        profile(),
        "acne",
        {},
        {
            "preferred_category": "moisturizer",
            "explicit_tolerated_ingredients": explicit["explicit_tolerated_ingredients"],
        },
    )

    assert explicit["explicit_tolerated_ingredients"] == ["niacinamide"]
    assert ranked[0]["name"] == "Com niacinamide"
    assert ranked[0]["score_breakdown"]["personalization"] > ranked[1]["score_breakdown"]["personalization"]


def test_fragrance_burns_excludes_fragrance_products() -> None:
    explicit = extract_explicit_user_preferences("fragrance minha pele arde")
    ranked = rank_recommendations_v3(
        [
            product("Com perfume", "moisturizer", ["fragrance", "glycerin"]),
            product("Sem perfume", "moisturizer", ["glycerin"]),
        ],
        profile(),
        "barrier",
        {},
        {
            "preferred_category": "moisturizer",
            "explicit_trigger_ingredients": explicit["explicit_trigger_ingredients"],
        },
    )

    assert explicit["explicit_trigger_ingredients"] == ["fragrance"]
    assert [item["name"] for item in ranked] == ["Sem perfume"]


def test_ranking_v3_generates_different_scores() -> None:
    ranked = rank_recommendations_v3(
        [
            product("Mais alinhado", "moisturizer", ["niacinamide", "glycerin"], price_range="low", compatibility_score=88),
            product("Basico", "moisturizer", ["glycerin"], price_range="mid", compatibility_score=72, irritation_risk=30),
        ],
        profile(),
        "acne",
        {},
        {"preferred_category": "moisturizer", "price_range": "low", "explicit_tolerated_ingredients": ["niacinamide"]},
    )

    assert ranked[0]["final_score"] != ranked[1]["final_score"]


def test_human_reasons_are_not_identical_for_all_products() -> None:
    ranked = rank_recommendations_v3(
        [
            product("Niacinamide Gel", "moisturizer", ["niacinamide", "glycerin"], price_range="low"),
            product("Barrier Cream", "moisturizer", ["ceramide", "panthenol"], price_range="mid"),
        ],
        profile(),
        "barrier",
        {},
        {"preferred_category": "moisturizer", "price_range": "low", "explicit_tolerated_ingredients": ["niacinamide"]},
    )

    assert ranked[0]["reason"] != ranked[1]["reason"]


def test_best_starting_option_explains_reason() -> None:
    ranked = rank_recommendations_v3(
        [
            product("Calmo", "moisturizer", ["niacinamide", "glycerin"], irritation_risk=5),
            product("Ok", "moisturizer", ["glycerin"], irritation_risk=20),
        ],
        profile(),
        "acne",
        {},
        {"preferred_category": "moisturizer", "explicit_tolerated_ingredients": ["niacinamide"]},
    )

    best = select_best_starting_option(ranked)
    assert best is not None
    assert best["name"] == "Calmo"
    assert "porque" in best["reason"]


def test_agent_recommendation_response_mentions_profile_category_tolerated_and_avoided(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(agent_service, "save_message", lambda *args, **kwargs: SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(
        agent_service,
        "build_agent_context",
        lambda db, user_id, skin_profile=None: {
            "skin_profile": skin_profile.model_dump(mode="json") if skin_profile else None,
            "personal_insights": {},
            "recent_analysis": [],
            "recent_feedbacks": [],
            "current_routine": None,
            "known_triggers": ["fragrance"],
            "tolerated_ingredients": ["niacinamide"],
            "ingredient_affinity": {"problematic": [], "well_tolerated": []},
            "recent_reactions": [],
            "recent_products_used": [],
            "user_goals": [],
            "conversation_summary": {},
            "context_status": "available",
        },
    )
    monkeypatch.setattr(
        agent_service,
        "recommend_products_tool",
        lambda *args, **kwargs: [
            {
                "product_id": str(uuid4()),
                "name": "Hidratante Leve",
                "brand": "Marca",
                "category": "moisturizer",
                "compatibility_score": 88,
                "irritation_risk": 8,
                "acne_risk": 6,
                "benefit_score": 80,
                "final_score": 91,
                "score_breakdown": {"compatibility": 88, "safety": 92, "goal_match": 70, "personalization": 90, "price": 100},
                "reason_codes": ["matches_requested_category", "avoids_explicit_trigger", "contains_explicit_tolerated_ingredient"],
                "reason": "É uma boa opção porque é um moisturizer leve, não contém os gatilhos que você citou e tem niacinamide.",
                "key_ingredients": ["niacinamide"],
            }
        ],
    )

    response = TestClient(app).post(
        "/agent/chat",
        json={
            "message": (
                "Eu usei um serum com niacinamide e minha pele ficou otima, mas fragrance minha pele arde. "
                "Agora quero um hidratante bom para pele oleosa, sensivel e com tendencia a acne, barato e sem fragrancia."
            ),
            "context": {"skin_profile": profile().model_dump(mode="json")},
        },
    )

    body = response.json()
    answer = body["answer"].lower()
    assert body["intent"] == AgentIntent.recommend_products
    assert "oleosa" in answer
    assert "moisturizer" in answer or "hidratante" in answer
    assert "niacinamide" in answer
    assert "fragrance" in answer
