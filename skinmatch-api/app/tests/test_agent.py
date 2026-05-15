from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.agent import memory as agent_memory
from app.modules.agent import service as agent_service
from app.modules.agent.planner import AgentPlan
from app.modules.agent.planner import (
    build_recommendation_constraints_from_message,
    detect_inci_list,
    detect_reaction_intent,
    extract_inci_from_message,
    plan_agent_response,
)
from app.modules.agent.quality import validate_agent_response
from app.modules.agent.response_templates import render_explain_reaction
from app.modules.agent.schemas import AgentChatRequest, AgentIntent
from app.modules.agent.schemas import EDUCATIONAL_DISCLAIMER


USER_ID = "00000000-0000-0000-0000-000000000001"


def payload(message: str = "Esse produto pode dar acne em mim?") -> dict:
    return {
        "user_id": USER_ID,
        "message": message,
        "context": {
            "product_name": "Serum Antiacne X",
            "brand": "Marca Y",
            "raw_ingredient_list": "Aqua, Niacinamide, Salicylic Acid, Fragrance",
            "skin_profile": {
                "skin_type": "oily",
                "sensitive_skin": True,
                "acne_prone": True,
                "barrier_compromised": False,
                "known_triggers": [],
                "tolerated_ingredients": ["niacinamide"],
            },
            "main_goal": "acne",
        },
    }


def fake_analysis_result() -> dict:
    return {
        "analysis_id": UUID("11111111-1111-1111-1111-111111111111"),
        "product_id": UUID("22222222-2222-2222-2222-222222222222"),
        "compatibility_score": 58,
        "verdict": "caution",
        "irritation_risk": 0.74,
        "acne_risk": 0.32,
        "benefit_score": 0.68,
        "barrier_support": 0.2,
        "applied_rules": ["RULE_001"],
        "positive_ingredients": ["niacinamide", "salicylic acid"],
        "warning_ingredients": ["fragrance"],
        "unknown_ingredients": [],
        "recommendation": "Faca teste de contato.",
        "disclaimer": EDUCATIONAL_DISCLAIMER,
    }


def patch_agent_dependencies(monkeypatch, calls: list[str] | None = None) -> None:
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(agent_service, "get_recent_messages", lambda db, user_id, limit=10: [])
    monkeypatch.setattr(
        agent_service,
        "build_agent_context",
        lambda db, user_id, skin_profile=None: {
            "skin_profile": skin_profile.model_dump(mode="json") if skin_profile else None,
            "personal_insights": {"total_feedbacks": 0, "common_triggers": [], "well_tolerated_ingredients": [], "patterns": []},
            "recent_analysis": [],
            "recent_feedbacks": [],
            "current_routine": None,
            "known_triggers": [],
            "tolerated_ingredients": [],
            "recent_reactions": [],
            "recent_products_used": [],
            "user_goals": [],
            "conversation_summary": {},
            "context_status": "insufficient_history",
        },
    )
    monkeypatch.setattr(agent_service, "save_message", lambda *args, **kwargs: SimpleNamespace(id=uuid4()))

    def fake_tool(*args, **kwargs):
        if calls is not None:
            calls.append("analyze_product")
        return fake_analysis_result()

    monkeypatch.setattr(agent_service, "analyze_product_tool", fake_tool)


def test_agent_chat_detects_analyze_product_with_formula(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)

    response = TestClient(app).post("/agent/chat", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "analyze_product"
    assert body["structured_result"]["compatibility_score"] == 58


def test_agent_chat_calls_analyze_product_tool(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)

    TestClient(app).post("/agent/chat", json=payload())

    assert calls == ["analyze_product"]


def test_agent_does_not_calculate_score_in_llm(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)
    monkeypatch.setattr(
        agent_service,
        "_openai_chat",
        lambda *args, **kwargs: "Eu explico o resultado da ferramenta sem mudar o score.",
    )

    response = TestClient(app).post("/agent/chat", json=payload())

    body = response.json()
    assert body["structured_result"]["compatibility_score"] == 58
    assert "compatibility_score" in body["structured_result"]


def test_agent_chat_returns_disclaimer(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)

    response = TestClient(app).post("/agent/chat", json=payload())

    body = response.json()
    assert EDUCATIONAL_DISCLAIMER in body["safety_disclaimer"]
    assert EDUCATIONAL_DISCLAIMER in body["answer"]


def test_safety_guardrail_blocks_swollen_face(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)

    response = TestClient(app).post("/agent/chat", json=payload("Meu rosto inchado e esta ardendo. O que faco?"))

    body = response.json()
    assert body["tools_used"] == []
    assert calls == []
    assert "procure orientacao medica" in body["answer"]


def test_memory_saves_user_and_assistant_messages(monkeypatch) -> None:
    saved: list[dict] = []
    patch_agent_dependencies(monkeypatch)

    def fake_save(*args, **kwargs):
        saved.append(kwargs)
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(agent_service, "save_message", fake_save)

    response = TestClient(app).post("/agent/chat", json=payload())

    assert response.status_code == 200
    assert [item["role"] for item in saved] == ["user", "assistant"]
    assert saved[1]["structured_result"]["compatibility_score"] == 58


def test_get_recent_messages_returns_latest_in_chronological_order() -> None:
    first = SimpleNamespace(
        id=uuid4(),
        user_id=UUID(USER_ID),
        role="user",
        content="primeira",
        intent=None,
        tools_used=[],
        structured_result=None,
        created_at=datetime(2026, 5, 3, 10, tzinfo=timezone.utc),
    )
    second = SimpleNamespace(
        id=uuid4(),
        user_id=UUID(USER_ID),
        role="assistant",
        content="segunda",
        intent=None,
        tools_used=[],
        structured_result=None,
        created_at=datetime(2026, 5, 3, 11, tzinfo=timezone.utc),
    )

    class FakeScalars:
        def all(self):
            return [second, first]

    class FakeDb:
        def scalars(self, statement):
            return FakeScalars()

    messages = agent_memory.get_recent_messages(FakeDb(), UUID(USER_ID), limit=2)

    assert [message.content for message in messages] == ["primeira", "segunda"]


def test_agent_formats_generate_routine_steps(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: "resposta generica do llm")
    monkeypatch.setattr(
        agent_service,
        "build_agent_context",
        lambda db, user_id, skin_profile=None: {"context_status": "available", "known_triggers": [], "tolerated_ingredients": []},
    )
    monkeypatch.setattr(agent_service, "get_recent_messages", lambda db, user_id, limit=10: [])
    monkeypatch.setattr(agent_service, "save_message", lambda *args, **kwargs: SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(
        agent_service,
        "generate_routine_tool",
        lambda *args, **kwargs: {
            "morning_routine": [
                {
                    "step": 1,
                    "type": "cleanser",
                    "product": {"id": str(uuid4()), "name": "Gel Suave", "brand": "Marca A"},
                    "instructions": "Use pela manha.",
                    "reason": "Remove oleosidade sem agredir.",
                }
            ],
            "night_routine": [
                {
                    "step": 1,
                    "type": "moisturizer",
                    "product": {"id": str(uuid4()), "name": "Creme Barreira", "brand": "Marca B"},
                    "instructions": "Aplique uma camada fina.",
                    "reason": "Ajuda a reforcar a barreira.",
                }
            ],
            "warnings": ["Introduza novos produtos gradualmente."],
        },
    )

    response = TestClient(app).post("/agent/chat", json=payload("Monte uma rotina simples"))

    body = response.json()
    assert body["tools_used"] == ["generate_routine"]
    assert "🌞 Rotina da manhã" in body["answer"]
    assert "Produto: Marca A Gel Suave" in body["answer"]
    assert "Como usar: Use pela manha." in body["answer"]
    assert "Por quê: Remove oleosidade sem agredir." in body["answer"]
    assert "⚠️ Cuidados" in body["answer"]
    assert "Montei uma rotina simples com" not in body["answer"]


def test_agent_explains_empty_routine(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        agent_service,
        "build_agent_context",
        lambda db, user_id, skin_profile=None: {"context_status": "available", "known_triggers": [], "tolerated_ingredients": []},
    )
    monkeypatch.setattr(agent_service, "get_recent_messages", lambda db, user_id, limit=10: [])
    monkeypatch.setattr(agent_service, "save_message", lambda *args, **kwargs: SimpleNamespace(id=uuid4()))
    monkeypatch.setattr(
        agent_service,
        "generate_routine_tool",
        lambda *args, **kwargs: {"morning_routine": [], "night_routine": [], "warnings": []},
    )

    response = TestClient(app).post("/agent/chat", json=payload("Monte uma rotina simples"))

    body = response.json()
    assert "Nenhuma etapa encontrada para manhã." in body["answer"]
    assert "Nenhuma etapa encontrada para noite." in body["answer"]
    assert "Nao encontrei produtos suficientes no catalogo" in body["answer"]


def test_product_without_formula_asks_for_formula_or_image(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)
    request = payload("Esse produto e bom para mim?")
    request["context"]["raw_ingredient_list"] = ""

    response = TestClient(app).post("/agent/chat", json=request)

    body = response.json()
    assert body["tools_used"] == []
    assert "lista INCI" in body["answer"] or "foto do rotulo" in body["answer"]
    assert body["missing_info"] == ["raw_ingredient_list"]
    assert calls == []


def test_analyze_plan_with_empty_formula_does_not_call_tool(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)
    request = payload("Esse produto pode piorar minha acne?")
    request["context"]["raw_ingredient_list"] = "   "

    response = TestClient(app).post("/agent/chat", json=request)

    body = response.json()
    assert response.status_code == 200
    assert body["tools_used"] == []
    assert body["missing_info"] == ["raw_ingredient_list"]
    assert "lista INCI" in body["answer"] or "foto do rotulo" in body["answer"]
    assert calls == []


def test_reaction_calls_insights_and_history(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        agent_service,
        "get_personal_insights_tool",
        lambda *args, **kwargs: calls.append("get_personal_insights") or {
            "total_feedbacks": 1,
            "common_triggers": [{"ingredient": "fragrance", "reaction": "irritation", "occurrences": 1}],
            "well_tolerated_ingredients": [],
            "patterns": ["fragrance apareceu associada a irritacao."],
        },
    )
    monkeypatch.setattr(
        agent_service,
        "get_analysis_history_tool",
        lambda *args, **kwargs: calls.append("get_analysis_history") or [],
    )

    response = TestClient(app).post("/agent/chat", json=payload("Minha pele ficou ardendo depois desse serum"))

    body = response.json()
    assert "get_personal_insights" in body["tools_used"]
    assert "get_analysis_history" in body["tools_used"]
    assert "pausar" in body["answer"] or "pause" in body["answer"]
    assert EDUCATIONAL_DISCLAIMER in body["answer"]


def test_alternatives_call_recommend_products(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        agent_service,
        "recommend_products_tool",
        lambda *args, **kwargs: calls.append("recommend_products") or [
            {
                "product_id": str(uuid4()),
                "name": "Gel Melhor",
                "brand": "Marca B",
                "compatibility_score": 88,
                "irritation_risk": 10,
                "acne_risk": 8,
                "benefit_score": 80,
                "reason": "Baixo risco",
                "key_ingredients": ["niacinamide"],
            }
        ],
    )

    response = TestClient(app).post("/agent/chat", json=payload("Me indique alternativas melhores"))

    body = response.json()
    assert calls == ["recommend_products"]
    assert body["tools_used"] == ["recommend_products"]
    assert "Gel Melhor" in body["answer"]


def test_recommendation_response_does_not_ask_for_inci(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)
    captured = {}
    monkeypatch.setattr(
        agent_service,
        "recommend_products_tool",
        lambda *args, **kwargs: captured.update(kwargs) or [
            {
                "product_id": str(uuid4()),
                "name": "Hidratante Leve",
                "brand": "Marca B",
                "compatibility_score": 88,
                "final_score": 90,
                "irritation_risk": 10,
                "acne_risk": 8,
                "benefit_score": 80,
                "score_breakdown": {
                    "compatibility": 88,
                    "goal_match": 80,
                    "safety": 90,
                    "personalization": 75,
                    "routine_fit": 80,
                    "price": 90,
                },
                "reason_codes": ["matches_price_range", "avoids_known_triggers"],
                "reason": "Boa opcao porque evita seus gatilhos.",
                "key_ingredients": ["niacinamide"],
            }
        ],
    )
    request = payload(
        "Quero um hidratante bom para pele oleosa, sensivel e com tendencia a acne, barato e sem fragrancia. O que voce recomenda?"
    )
    request["context"]["raw_ingredient_list"] = ""

    response = TestClient(app).post("/agent/chat", json=request)

    body = response.json()
    assert body["intent"] == "recommend_products"
    assert body["tools_used"] == ["recommend_products"]
    assert "lista INCI" not in body["answer"]
    assert "foto do rotulo" not in body["answer"]
    assert captured["constraints"]["preferred_category"] == "moisturizer"
    assert captured["constraints"]["price_range"] == "low"
    assert "fragrance" in captured["exclude_ingredients"]


def test_insufficient_history_is_explicit(monkeypatch) -> None:
    patch_agent_dependencies(monkeypatch)
    monkeypatch.setattr(
        agent_service,
        "get_personal_insights_tool",
        lambda *args, **kwargs: {
            "total_feedbacks": 0,
            "common_triggers": [],
            "well_tolerated_ingredients": [],
            "patterns": [],
        },
    )

    response = TestClient(app).post("/agent/chat", json=payload("Quais ingredientes minha pele nao tolera bem?"))

    body = response.json()
    assert "poucos dados" in body["answer"].lower()
    assert "fingir" in body["answer"].lower() or "nao vou" in body["answer"].lower()


def test_quality_checker_flags_missing_next_step() -> None:
    failures = validate_agent_response(
        f"Resposta qualquer. {EDUCATIONAL_DISCLAIMER}",
        intent=AgentIntent.analyze_product,
        tools_used=["analyze_product"],
        structured_result={"compatibility_score": 80},
        confidence="high",
    )

    assert "missing_practical_next_step" in failures


def test_quality_checker_forces_safe_fallback_when_correction_fails(monkeypatch) -> None:
    monkeypatch.setattr(agent_service, "_openai_chat", lambda *args, **kwargs: "Resposta ruim sem disclaimer")
    answer = agent_service.generate_planned_answer(
        payload("Esse produto pode dar acne em mim?"),
        AgentPlan(intent=AgentIntent.analyze_product, confidence="high", tools_needed=["analyze_product"]),
        [],
        None,
        {"context_status": "available"},
    )

    assert "Proximo passo" in answer
    assert EDUCATIONAL_DISCLAIMER in answer


def test_reaction_with_inci_in_message_is_explain_reaction_and_analyzes(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)
    message = (
        "Comecei a ter ardencia e umas espinhas depois de usar esse produto: "
        "Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat., Parfum. "
        "Minha pele e oleosa, sensivel e ja tive problema com fragrancia antes. "
        "O que pode estar acontecendo e o que eu faco agora?"
    )
    request = payload(message)
    request["context"]["raw_ingredient_list"] = ""
    monkeypatch.setattr(
        agent_service,
        "get_personal_insights_tool",
        lambda *args, **kwargs: {
            "total_feedbacks": 1,
            "common_triggers": [{"ingredient": "fragrance", "reaction": "irritation", "occurrences": 1}],
            "well_tolerated_ingredients": [],
            "patterns": [],
        },
    )
    monkeypatch.setattr(agent_service, "get_analysis_history_tool", lambda *args, **kwargs: [])

    response = TestClient(app).post("/agent/chat", json=request)

    body = response.json()
    assert body["intent"] == "explain_reaction"
    assert "analyze_product" in body["tools_used"]
    assert "get_personal_insights" in body["tools_used"]
    assert "get_analysis_history" in body["tools_used"]
    assert "lista INCI" not in body["answer"]
    assert "fragrance" in body["answer"].lower() or "parfum" in body["answer"].lower()
    assert "pause" in body["answer"].lower()
    assert calls == ["analyze_product"]


def test_reaction_with_formula_in_context_uses_analyze_product(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)
    monkeypatch.setattr(agent_service, "get_personal_insights_tool", lambda *args, **kwargs: {"common_triggers": [], "well_tolerated_ingredients": [], "patterns": [], "total_feedbacks": 0})
    monkeypatch.setattr(agent_service, "get_analysis_history_tool", lambda *args, **kwargs: [])

    response = TestClient(app).post("/agent/chat", json=payload("Comecei a ter espinhas depois desse produto"))

    body = response.json()
    assert body["intent"] == "explain_reaction"
    assert "analyze_product" in body["tools_used"]


def test_ingredient_question_is_explain_ingredients() -> None:
    request = AgentChatRequest(message="O que niacinamide faz?")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.explain_ingredients


def test_routine_message_is_generate_routine() -> None:
    request = AgentChatRequest(message="monte uma rotina simples")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.generate_routine


def test_recommendation_message_is_recommend_products() -> None:
    request = AgentChatRequest(message="me indique alternativas sem fragrancia")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.recommend_products


def test_moisturizer_cheap_fragrance_free_recommendation_plan() -> None:
    message = (
        "Eu usei um serum com niacinamide e minha pele ficou otima, mas sempre que uso produtos com fragrance minha pele arde. "
        "Agora quero um hidratante bom para pele oleosa, sensivel e com tendencia a acne, de preferencia barato e sem fragrancia. "
        "O que voce recomenda?"
    )
    request = AgentChatRequest(message=message)
    plan = plan_agent_response(
        request,
        {
            "context_status": "available",
            "known_triggers": ["fragrance"],
            "tolerated_ingredients": ["niacinamide"],
            "ingredient_affinity": {
                "problematic": [{"ingredient_name": "fragrance", "confidence": 0.9}],
                "well_tolerated": [{"ingredient_name": "niacinamide", "confidence": 0.9}],
            },
        },
    )

    assert plan.intent == AgentIntent.recommend_products
    assert "recommend_products" in plan.tools_needed
    assert "raw_ingredient_list" not in plan.missing_info
    assert "fragrance" in plan.recommendation_payload["exclude_ingredients"]
    assert plan.recommendation_payload["constraints"]["preferred_category"] == "moisturizer"
    assert plan.recommendation_payload["constraints"]["price_range"] == "low"


def test_sunscreen_oily_recommendation_constraints() -> None:
    payload = build_recommendation_constraints_from_message("quero um protetor para pele oleosa")

    assert payload["constraints"]["preferred_category"] == "sunscreen"
    assert payload["main_goal"] == "oil_control"


def test_analyze_this_product_with_inci_is_analyze_product() -> None:
    request = AgentChatRequest(message="analise esse produto: Aqua, Glycerin, Niacinamide")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.analyze_product


def test_reaction_this_product_with_inci_is_explain_reaction() -> None:
    request = AgentChatRequest(message="esse produto me deu ardencia: Aqua, Glycerin, Fragrance")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.explain_reaction
    assert "analyze_product" in plan.tools_needed


def test_alternatives_without_formula_are_recommendations() -> None:
    request = AgentChatRequest(message="me indique alternativas melhores para esse produto")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.recommend_products
    assert "raw_ingredient_list" not in plan.missing_info


def test_missing_info_sets_low_confidence() -> None:
    request = AgentChatRequest(message="esse produto pode piorar minha acne?")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.missing_info
    assert plan.confidence == "low"


def test_safety_urgent_blocks_cosmetic_tools(monkeypatch) -> None:
    calls: list[str] = []
    patch_agent_dependencies(monkeypatch, calls)

    response = TestClient(app).post("/agent/chat", json=payload("Estou com rosto inchado e falta de ar, monte uma rotina"))

    body = response.json()
    assert body["risk_level"] == "high"
    assert body["tools_used"] == []
    assert "procure orientacao medica" in body["answer"]
    assert calls == []


def test_inci_without_reaction_is_analyze_product() -> None:
    request = AgentChatRequest(message="Aqua, Glycerin, Niacinamide, Panthenol")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.analyze_product


def test_reaction_without_formula_asks_single_formula_question() -> None:
    request = AgentChatRequest(message="Minha pele ficou ardendo e ressecou")
    plan = plan_agent_response(request, {"context_status": "available"})

    assert plan.intent == AgentIntent.explain_reaction
    assert plan.should_ask_clarifying_question is True
    assert plan.missing_info == ["raw_ingredient_list"]
    assert plan.clarifying_question.count("?") == 1


def test_extract_inci_from_reaction_message() -> None:
    message = "Comecei a ter ardencia depois de usar: Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat., Parfum. O que faco?"

    assert detect_reaction_intent(message) is True
    assert detect_inci_list(message) is True
    assert extract_inci_from_message(message) == "Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat, Parfum"


def reaction_text(irritation_risk=0.74, triggers=None) -> str:
    return render_explain_reaction(
        {
            "analysis": {
                "irritation_risk": irritation_risk,
                "verdict": "caution",
                "warning_ingredients": ["fragrance", "fragrance", "alcohol denat"],
                "applied_rules": ["RULE_001"],
            },
            "insights": {
                "common_triggers": triggers if triggers is not None else [{"ingredient": "fragrance"}],
                "well_tolerated_ingredients": [],
                "patterns": [],
            },
            "history": [],
        },
        {
            "skin_profile": {
                "skin_type": "oily",
                "sensitive_skin": True,
                "acne_prone": True,
                "barrier_compromised": False,
            },
            "known_triggers": ["fragrance"],
        },
    )


def test_reaction_suspicious_ingredients_are_deduplicated() -> None:
    answer = reaction_text()
    suspicious_line = next(line for line in answer.splitlines() if line.startswith("Causas provaveis"))

    assert suspicious_line.lower().count("fragrance (parfum)") == 1


def test_alcohol_denat_appears_when_cited_by_rules() -> None:
    answer = reaction_text()
    suspicious_line = next(line for line in answer.splitlines() if line.startswith("Causas provaveis"))

    assert "alcohol denat" in suspicious_line.lower()


def test_irritation_risk_fraction_becomes_percent() -> None:
    answer = reaction_text(irritation_risk=0.74)

    assert "risco de irritacao estimado: alto" in answer


def test_irritation_risk_one_does_not_appear_as_loose_one() -> None:
    answer = reaction_text(irritation_risk=1.0)

    assert "risco de irritacao 1" not in answer.lower()
    assert "100/100" not in answer
    assert "risco de irritacao estimado: alto" in answer


def test_history_message_with_feedback_trigger() -> None:
    answer = reaction_text(triggers=[{"ingredient": "fragrance"}])

    assert "No seu historico, Fragrance (parfum) aparece como possivel gatilho." in answer


def test_history_message_without_feedbacks() -> None:
    answer = reaction_text(triggers=[])

    assert "Ainda nao ha feedbacks suficientes no seu historico para confirmar um padrao pessoal." in answer


def test_reaction_response_prioritizes_main_suspect_and_personalizes_profile() -> None:
    answer = reaction_text()

    assert "principal suspeito: Fragrance (parfum)" in answer
    assert "como sua pele e oleosa, sensivel, com tendencia a acne" in answer
    assert "Salicylic acid" in answer
    assert "Alcohol denat." in answer
