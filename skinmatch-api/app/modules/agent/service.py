import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.modules.agent.context_builder import build_agent_context
from app.modules.agent.memory import get_recent_messages, save_message
from app.modules.agent.planner import (
    AgentPlan,
    build_recommendation_constraints_from_message,
    extract_inci_from_message,
    plan_agent_response,
)
from app.modules.agent.prompts import INTENT_PROMPT, SYSTEM_PROMPT
from app.modules.agent.quality import safe_fallback, validate_agent_response
from app.modules.agent.response_templates import follow_up_for_intent, render_template
from app.modules.agent.schemas import (
    EDUCATIONAL_DISCLAIMER,
    AgentChatRequest,
    AgentChatResponse,
    AgentIntent,
)
from app.modules.agent.tools import (
    adjust_routine_tool,
    analyze_product_tool,
    generate_routine_tool,
    get_analysis_history_tool,
    get_current_routine_tool,
    get_personal_insights_tool,
    recommend_products_tool,
)


SERIOUS_SIGNAL_TERMS = [
    "queimadura",
    "inchaco",
    "inchaço",
    "falta de ar",
    "ferida aberta",
    "dor intensa",
    "alergia forte",
    "rosto inchado",
]


def has_serious_signal(message: str) -> bool:
    normalized = message.lower()
    return any(term in normalized for term in SERIOUS_SIGNAL_TERMS)


def fallback_detect_intent(request: AgentChatRequest) -> AgentIntent:
    text = request.message.lower()
    has_formula = bool(request.context.raw_ingredient_list)
    if any(word in text for word in ["rotina", "manha", "noite", "passo a passo"]):
        return AgentIntent.generate_routine
    if any(word in text for word in ["alternativa", "alternativas", "recomende", "indique", "melhores"]):
        return AgentIntent.recommend_products
    if any(word in text for word in ["historico", "histórico", "toler", "gatilho", "insight"]):
        return AgentIntent.get_personal_insights
    if any(word in text for word in ["ardeu", "ardendo", "irritou", "vermelha", "reacao", "reação"]):
        return AgentIntent.explain_reaction
    if has_formula or any(word in text for word in ["produto", "formula", "fórmula", "acne", "cravo"]):
        return AgentIntent.analyze_product
    if len(text.strip()) < 8:
        return AgentIntent.unknown
    return AgentIntent.general_skincare_question


def _openai_chat(messages: list[dict[str, str]], temperature: float = 0.2) -> str | None:
    if not settings.openai_api_key:
        return None

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.agent_model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"]).strip()
    except Exception:
        return None


def detect_intent(request: AgentChatRequest) -> AgentIntent:
    llm_answer = _openai_chat(
        [
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": request.message},
        ],
        temperature=0,
    )
    if llm_answer:
        value = llm_answer.strip().lower()
        try:
            return AgentIntent(value)
        except ValueError:
            pass
    return fallback_detect_intent(request)


def _goal_from_message(message: str, default: str | None = None) -> str:
    text = message.lower()
    if "acne" in text or "cravo" in text:
        return "acne"
    if "oleos" in text:
        return "oil_control"
    if "barreira" in text or "ardendo" in text or "sensivel" in text or "sensível" in text:
        return "barrier"
    return default or "general"


def recommendation_constraints_from_message(message: str, exclude_ingredients: list[str] | None = None) -> dict[str, Any]:
    payload = build_recommendation_constraints_from_message(message)
    excluded = set(payload.get("exclude_ingredients", [])) | set(exclude_ingredients or [])
    constraints = dict(payload.get("constraints", {}))
    constraints["exclude_ingredients"] = sorted(excluded)
    return constraints


def _needs_formula_response(intent: AgentIntent) -> AgentChatResponse:
    return AgentChatResponse(
        answer=(
            "Para analisar esse produto com seguranca, preciso da lista INCI completa. "
            "Voce pode colar a formula ou enviar uma foto do rotulo."
        ),
        intent=intent,
        tools_used=[],
        structured_result=None,
    )


def _has_formula_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _format_routine_section(title: str, empty_message: str, steps: list[dict[str, Any]]) -> str:
    lines = [title, ""]
    if not steps:
        lines.append(empty_message)
        return "\n".join(lines)

    for index, step in enumerate(steps, start=1):
        step_type = step.get("type") or "etapa"
        product = step.get("product")
        instructions = step.get("instructions") or "Introduza gradualmente e observe a resposta da pele."
        reason = step.get("reason") or "Selecionado com base na compatibilidade estimada."
        lines.append(f"{index}. [{step_type}]")
        if product:
            brand = str(product.get("brand") or "").strip()
            name = str(product.get("name") or "").strip()
            product_name = " ".join(part for part in [brand, name] if part)
            if product_name:
                lines.append(f"Produto: {product_name}")
        lines.append(f"Como usar: {instructions}")
        lines.append(f"Por quê: {reason}")
        lines.append("")
    return "\n".join(lines).strip()


def format_routine_result(routine_result: Any) -> str:
    if not isinstance(routine_result, dict):
        return (
            "Nao encontrei uma rotina estruturada para exibir. "
            f"{EDUCATIONAL_DISCLAIMER}"
        )

    morning = routine_result.get("morning_routine") or []
    night = routine_result.get("night_routine") or []
    warnings = routine_result.get("warnings") or []
    has_any_step = bool(morning or night)

    sections = [
        _format_routine_section("🌞 Rotina da manhã", "Nenhuma etapa encontrada para manhã.", morning),
        _format_routine_section("🌙 Rotina da noite", "Nenhuma etapa encontrada para noite.", night),
        "⚠️ Cuidados",
    ]

    if warnings:
        sections.extend(f"- {warning}" for warning in warnings)
    else:
        sections.append("- Introduza novos produtos gradualmente.")

    if not has_any_step:
        sections.append("")
        sections.append("Nao encontrei produtos suficientes no catalogo para montar uma rotina completa com os filtros atuais.")

    sections.append("")
    sections.append(EDUCATIONAL_DISCLAIMER)
    return "\n\n".join(sections)


def execute_tool(db: Session, request: AgentChatRequest, intent: AgentIntent) -> tuple[list[str], Any | None]:
    context = request.context
    goal = context.main_goal or _goal_from_message(request.message)

    if intent in {AgentIntent.analyze_product, AgentIntent.explain_reaction}:
        if not context.raw_ingredient_list:
            return [], None
        return [
            "analyze_product"
        ], analyze_product_tool(
            db,
            user_id=request.user_id,
            product_name=context.product_name,
            brand=context.brand,
            raw_ingredient_list=context.raw_ingredient_list,
            main_goal=goal,
            skin_profile=context.skin_profile,
        )

    if intent == AgentIntent.recommend_products:
        return [
            "recommend_products"
        ], recommend_products_tool(
            db,
            user_id=request.user_id,
            main_goal=goal,
            exclude_ingredients=context.exclude_ingredients,
            constraints=recommendation_constraints_from_message(request.message, context.exclude_ingredients),
            limit=5,
            skin_profile=context.skin_profile,
        )

    if intent == AgentIntent.generate_routine:
        return [
            "generate_routine"
        ], generate_routine_tool(
            db,
            user_id=request.user_id,
            main_goal=goal,
            constraints={"avoid_ingredients": context.exclude_ingredients, "max_steps": 5},
            skin_profile=context.skin_profile,
        )

    if intent == AgentIntent.get_personal_insights:
        return ["get_personal_insights"], get_personal_insights_tool(db, user_id=request.user_id)

    return [], None


def execute_plan_tools(
    db: Session,
    request: AgentChatRequest,
    plan: AgentPlan,
    agent_context: dict | None = None,
) -> tuple[list[str], Any | None]:
    context = request.context
    recommendation_payload = plan.recommendation_payload or build_recommendation_constraints_from_message(
        request.message,
        agent_context or {},
    )
    goal = context.main_goal or recommendation_payload.get("main_goal") or _goal_from_message(request.message)
    tools_used: list[str] = []

    if plan.intent == AgentIntent.analyze_product and "analyze_product" in plan.tools_needed:
        if not _has_formula_text(context.raw_ingredient_list):
            return [], None
        tools_used.append("analyze_product")
        return tools_used, analyze_product_tool(
            db,
            user_id=request.user_id,
            product_name=context.product_name,
            brand=context.brand,
            raw_ingredient_list=context.raw_ingredient_list,
            main_goal=goal,
            skin_profile=context.skin_profile,
        )

    if plan.intent == AgentIntent.explain_reaction:
        result: dict[str, Any] = {}
        if "analyze_product" in plan.tools_needed and context.raw_ingredient_list:
            tools_used.append("analyze_product")
            result["analysis"] = analyze_product_tool(
                db,
                user_id=request.user_id,
                product_name=context.product_name,
                brand=context.brand,
                raw_ingredient_list=context.raw_ingredient_list,
                main_goal=goal,
                skin_profile=context.skin_profile,
            )
        if "get_personal_insights" in plan.tools_needed:
            tools_used.append("get_personal_insights")
            result["insights"] = get_personal_insights_tool(db, user_id=request.user_id)
        if "get_analysis_history" in plan.tools_needed:
            tools_used.append("get_analysis_history")
            result["history"] = get_analysis_history_tool(db, user_id=request.user_id, limit=5)
        return tools_used, result

    if plan.intent == AgentIntent.recommend_products:
        constraints = recommendation_payload.get("constraints", {})
        exclude_ingredients = sorted(
            set(context.exclude_ingredients)
            | set(recommendation_payload.get("exclude_ingredients", []))
            | set(constraints.get("exclude_ingredients", []))
        )
        constraints = {**constraints, "exclude_ingredients": exclude_ingredients}
        tools_used.append("recommend_products")
        return tools_used, recommend_products_tool(
            db,
            user_id=request.user_id,
            main_goal=goal,
            exclude_ingredients=exclude_ingredients,
            constraints=constraints,
            limit=5,
            skin_profile=context.skin_profile,
        )

    if plan.intent == AgentIntent.generate_routine:
        tools_used.append("generate_routine")
        return tools_used, generate_routine_tool(
            db,
            user_id=request.user_id,
            main_goal=goal,
            constraints={"avoid_ingredients": context.exclude_ingredients, "max_steps": 5},
            skin_profile=context.skin_profile,
        )

    if plan.intent == AgentIntent.adjust_routine:
        tools_used.extend(["get_current_routine", "adjust_routine"])
        return tools_used, adjust_routine_tool(
            db,
            user_id=request.user_id,
            main_goal=goal,
            constraints={"avoid_ingredients": context.exclude_ingredients, "max_steps": 4},
            skin_profile=context.skin_profile,
        )

    if plan.intent in {AgentIntent.get_personal_insights, AgentIntent.explain_ingredients}:
        tools_used.append("get_personal_insights")
        return tools_used, get_personal_insights_tool(db, user_id=request.user_id)

    return [], None


def fallback_answer(intent: AgentIntent, structured_result: Any | None, tools_used: list[str]) -> str:
    if intent in {AgentIntent.analyze_product, AgentIntent.explain_reaction} and isinstance(structured_result, dict):
        warnings = ", ".join(structured_result.get("warning_ingredients", [])[:3]) or "sem alertas principais"
        positives = ", ".join(structured_result.get("positive_ingredients", [])[:3]) or "sem ativos positivos claros"
        return (
            f"Com base na ferramenta de analise, o score estimado foi {structured_result.get('compatibility_score')} "
            f"e o veredito foi {structured_result.get('verdict')}. O produto pode ter pontos positivos como "
            f"{positives}, mas merece atencao por {warnings}. {structured_result.get('recommendation', '')} "
            f"{EDUCATIONAL_DISCLAIMER}"
        ).strip()

    if intent == AgentIntent.recommend_products and isinstance(structured_result, list):
        if not structured_result:
            return f"Nao encontrei alternativas suficientes com os filtros atuais. {EDUCATIONAL_DISCLAIMER}"
        top = structured_result[0]
        score = top.get("final_score", top.get("compatibility_score"))
        return (
            f"A melhor alternativa encontrada foi {top.get('name')} da {top.get('brand')}, com score "
            f"{score}. Motivo: {top.get('reason')}. {EDUCATIONAL_DISCLAIMER}"
        )

    if intent == AgentIntent.generate_routine and isinstance(structured_result, dict):
        return format_routine_result(structured_result)

    if intent == AgentIntent.get_personal_insights and isinstance(structured_result, dict):
        total = structured_result.get("total_feedbacks", 0)
        patterns = structured_result.get("patterns", [])
        first = patterns[0] if patterns else "Ainda preciso de mais feedbacks para identificar padroes fortes."
        return f"Encontrei {total} feedbacks no seu historico. {first} {EDUCATIONAL_DISCLAIMER}"

    if intent == AgentIntent.unknown:
        return "Pode me dar um pouco mais de contexto ou colar a formula do produto? Assim eu consigo te ajudar melhor."

    return (
        "Posso ajudar analisando uma formula, sugerindo alternativas, gerando uma rotina ou olhando seus insights pessoais. "
        f"{EDUCATIONAL_DISCLAIMER}"
    )


def generate_final_answer(
    request: AgentChatRequest,
    intent: AgentIntent,
    tools_used: list[str],
    structured_result: Any | None,
    recent_messages: list[Any],
) -> str:
    if "generate_routine" in tools_used:
        return format_routine_result(structured_result)

    tool_context = json.dumps(structured_result, ensure_ascii=False, default=str)[:6000]
    memory_context = "\n".join(f"{item.role}: {item.content}" for item in recent_messages[-6:])
    llm_answer = _openai_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Historico recente:\n{memory_context}\n\n"
                    f"Mensagem atual: {request.message}\n"
                    f"Intencao: {intent.value}\n"
                    f"Ferramentas usadas: {tools_used}\n"
                    f"Resultado estruturado das ferramentas: {tool_context}\n\n"
                    "Explique o resultado sem recalcular scores e sem inventar dados."
                ),
            },
        ],
        temperature=0.3,
    )
    if llm_answer:
        if EDUCATIONAL_DISCLAIMER not in llm_answer:
            llm_answer = f"{llm_answer}\n\n{EDUCATIONAL_DISCLAIMER}"
        return llm_answer
    return fallback_answer(intent, structured_result, tools_used)


def generate_planned_answer(
    request: AgentChatRequest,
    plan: AgentPlan,
    tools_used: list[str],
    structured_result: Any | None,
    agent_context: dict,
) -> str:
    base_answer = render_template(plan.intent, structured_result, agent_context)
    failures = validate_agent_response(
        base_answer,
        intent=plan.intent,
        tools_used=tools_used,
        structured_result=structured_result,
        confidence=plan.confidence,
    )
    if not failures:
        return base_answer

    correction = _openai_chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Corrija a resposta abaixo. Problemas: {failures}. "
                    "Inclua disclaimer, limitacao se a confianca for baixa e um proximo passo pratico. "
                    "Nao invente score nem historico.\n\n"
                    f"Intencao: {plan.intent.value}\n"
                    f"Tools usadas: {tools_used}\n"
                    f"Resultado estruturado: {json.dumps(structured_result, ensure_ascii=False, default=str)[:5000]}\n"
                    f"Resposta atual: {base_answer}"
                ),
            },
        ],
        temperature=0.2,
    )
    if correction:
        second_failures = validate_agent_response(
            correction,
            intent=plan.intent,
            tools_used=tools_used,
            structured_result=structured_result,
            confidence=plan.confidence,
        )
        if not second_failures:
            return correction
    return safe_fallback(plan.intent, plan.confidence)


def _response_confidence(plan: AgentPlan, tools_used: list[str], structured_result: Any | None) -> str:
    if plan.missing_info:
        return "low"
    if tools_used and structured_result:
        if plan.intent == AgentIntent.recommend_products and isinstance(structured_result, list) and not structured_result:
            return "low"
        return "high"
    if plan.intent not in {AgentIntent.unknown, AgentIntent.general_question}:
        return "medium"
    return "low"


def chat(db: Session, request: AgentChatRequest) -> AgentChatResponse:
    extracted_formula = extract_inci_from_message(request.message)
    if extracted_formula and not request.context.raw_ingredient_list:
        request.context.raw_ingredient_list = extracted_formula

    agent_context = build_agent_context(db, request.user_id, request.context.skin_profile)
    if has_serious_signal(request.message):
        answer = (
            "Isso pode indicar uma reacao importante. Interrompa o uso do produto e procure orientacao "
            "medica/dermatologica, especialmente se houver dor intensa, inchaco, feridas ou dificuldade para respirar."
        )
        save_message(db, user_id=request.user_id, role="user", content=request.message)
        response = AgentChatResponse(
            answer=answer,
            intent=AgentIntent.unknown,
            tools_used=[],
            structured_result=None,
            confidence="high",
            risk_level="high",
            follow_up_suggestion=None,
            context_status=agent_context.get("context_status", "available"),
        )
        save_message(
            db,
            user_id=request.user_id,
            role="assistant",
            content=response.answer,
            intent=response.intent.value,
            confidence=response.confidence,
            tools_used=response.tools_used,
            user_context_snapshot=agent_context,
        )
        return response

    plan = plan_agent_response(request, agent_context)
    if plan.recommendation_payload:
        agent_context["recommendation_payload"] = plan.recommendation_payload
    if "analyze_product" in plan.tools_needed and not _has_formula_text(request.context.raw_ingredient_list):
        plan.missing_info = ["raw_ingredient_list"]
        plan.confidence = "low"
        plan.should_ask_clarifying_question = True
        plan.clarifying_question = "Pode colar a lista INCI completa ou enviar uma foto do rotulo?"

    if plan.should_ask_clarifying_question and plan.missing_info:
        answer = (
            f"{plan.clarifying_question}\n\n"
            "Tenho poucos dados para responder sem inventar resultado.\n\n"
            f"{EDUCATIONAL_DISCLAIMER}"
        )
        response = AgentChatResponse(
            answer=answer,
            intent=plan.intent,
            tools_used=[],
            structured_result=None,
            confidence=plan.confidence,
            missing_info=plan.missing_info,
            follow_up_suggestion=plan.clarifying_question,
            context_status=agent_context.get("context_status", "available"),
            risk_level=plan.risk_level,
        )
        save_message(
            db,
            user_id=request.user_id,
            role="user",
            content=request.message,
            intent=plan.intent.value,
            confidence=plan.confidence,
            user_context_snapshot=agent_context,
        )
        save_message(
            db,
            user_id=request.user_id,
            role="assistant",
            content=response.answer,
            intent=response.intent.value,
            confidence=response.confidence,
            tools_used=response.tools_used,
            structured_result=response.structured_result,
            user_context_snapshot=agent_context,
        )
        return response

    tools_used, structured_result = execute_plan_tools(db, request, plan, agent_context)
    confidence = _response_confidence(plan, tools_used, structured_result)

    response = AgentChatResponse(
        answer=generate_planned_answer(request, plan, tools_used, structured_result, agent_context),
        intent=plan.intent,
        tools_used=tools_used,
        structured_result=structured_result,
        confidence=confidence,
        missing_info=plan.missing_info,
        follow_up_suggestion=follow_up_for_intent(plan.intent),
        context_status=agent_context.get("context_status", "available"),
        risk_level=plan.risk_level,
    )

    save_message(
        db,
        user_id=request.user_id,
        role="user",
        content=request.message,
        intent=plan.intent.value,
        confidence=plan.confidence,
        user_context_snapshot=agent_context,
    )
    save_message(
        db,
        user_id=request.user_id,
        role="assistant",
        content=response.answer,
        intent=response.intent.value,
        confidence=response.confidence,
        tools_used=response.tools_used,
        structured_result=response.structured_result,
        user_context_snapshot=agent_context,
    )
    return response
