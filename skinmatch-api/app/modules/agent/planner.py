from pydantic import BaseModel, Field

from app.modules.agent.schemas import AgentChatRequest, AgentIntent


REACTION_TERMS = [
    "ardência",
    "ardencia",
    "ardor",
    "ardeu",
    "ardendo",
    "queimando",
    "queimadura",
    "irritação",
    "irritacao",
    "vermelho",
    "vermelha",
    "vermelhidão",
    "vermelhidao",
    "coceira",
    "piorou",
    "ressecou",
    "descamou",
    "reação",
    "reacao",
]
SAFETY_URGENT_TERMS = ["rosto inchado", "falta de ar", "dor intensa", "ferida aberta", "alergia forte"]
INCI_MARKERS = [
    "aqua",
    "glycerin",
    "niacinamide",
    "salicylic acid",
    "glycolic acid",
    "alcohol denat",
    "parfum",
    "fragrance",
    "retinol",
    "panthenol",
    "ceramide",
]
PREFERENCE_INGREDIENTS = [
    "niacinamide",
    "fragrance",
    "parfum",
    "perfume",
    "alcohol denat",
    "retinol",
    "salicylic acid",
    "azelaic acid",
    "ceramide",
    "panthenol",
    "glycerin",
    "zinc pca",
]


class AgentPlan(BaseModel):
    intent: AgentIntent
    confidence: str = "medium"
    missing_info: list[str] = Field(default_factory=list)
    tools_needed: list[str] = Field(default_factory=list)
    should_ask_clarifying_question: bool = False
    clarifying_question: str = ""
    answer_strategy: str = ""
    risk_level: str = "low"
    recommendation_payload: dict = Field(default_factory=dict)


def detect_safety_urgent(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in SAFETY_URGENT_TERMS)


def detect_reaction_intent(message: str) -> bool:
    text = message.lower()
    if any(term in text for term in REACTION_TERMS):
        return True
    acne_reaction_context = any(term in text for term in ["comecei", "depois", "surgiu", "surgiram", "tive", "piorou", "apareceu", "apareceram"])
    return acne_reaction_context and any(term in text for term in ["espinha", "espinhas", "acne"])


def detect_inci_list(message: str) -> bool:
    text = message.lower()
    return "," in text and any(marker in text for marker in INCI_MARKERS)


def detect_routine_intent(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in ["rotina", "manha", "manhã", "noite", "passo a passo"])


def detect_recommendation_intent(message: str) -> bool:
    text = message.lower()
    return any(
        term in text
        for term in [
            "alternativa",
            "alternativas",
            "recomende",
            "indique",
            "melhores",
            "comprar",
            "opcao",
            "opção",
            "barata",
            "barato",
            "barata",
            "hidratante",
            "protetor",
            "cleanser",
            "limpador",
            "sabonete",
            "gel de limpeza",
            "sérum",
            "serum",
            "tratamento",
            "indicação",
            "indicacao",
            "o que você recomenda",
            "o que voce recomenda",
            "qual produto",
            "melhor produto",
            "opções",
            "opcoes",
            "mais seguro",
            "sem fragr",
        ]
    )


def detect_specific_product_analysis_intent(message: str, context_raw_ingredient_list: str | None = None) -> bool:
    text = message.lower()
    if detect_inci_list(message):
        return True
    asks_this_product = any(term in text for term in ["esse produto", "este produto", "essa formula", "essa fórmula"])
    wants_analysis = any(term in text for term in ["analise", "analisar", "e bom para mim", "é bom para mim", "pode dar acne", "piorar minha acne"])
    has_context_formula = bool(context_raw_ingredient_list and context_raw_ingredient_list.strip())
    return asks_this_product and wants_analysis and has_context_formula


def detect_forward_recommendation_request(message: str) -> bool:
    text = message.lower()
    return any(
        term in text
        for term in [
            "quero",
            "recomenda",
            "recomende",
            "indique",
            "indicação",
            "indicacao",
            "qual produto",
            "melhor produto",
            "comprar",
            "opções",
            "opcoes",
            "o que voce recomenda",
            "o que você recomenda",
        ]
    )


def detect_skin_profile_mentions(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in ["pele oleosa", "sensivel", "sensível", "acne", "espinha", "cravo", "barreira"])


def detect_product_category_request(message: str) -> str | None:
    text = message.lower()
    if any(term in text for term in ["hidratante", "creme", "gel hidratante"]):
        return "moisturizer"
    if any(term in text for term in ["protetor", "sunscreen", "fps", "spf"]):
        return "sunscreen"
    if any(term in text for term in ["limpador", "limpeza", "sabonete", "gel de limpeza", "cleanser"]):
        return "cleanser"
    if any(term in text for term in ["sérum", "serum", "tratamento", "ácido", "acido"]):
        return "treatment"
    return None


def detect_price_constraint(message: str) -> str | None:
    text = message.lower()
    if any(term in text for term in ["barato", "barata", "acessivel", "acessível", "economico", "econômico"]):
        return "low"
    if any(term in text for term in ["intermediario", "intermediário", "custo beneficio", "custo benefício"]):
        return "mid"
    if any(term in text for term in ["premium", "caro", "cara"]):
        return "high"
    return None


def detect_excluded_ingredients(message: str) -> list[str]:
    text = message.lower()
    excluded: set[str] = set()
    if any(term in text for term in ["sem fragrância", "sem fragrancia", "sem perfume", "sem parfum", "fragrance free"]):
        excluded.add("fragrance")
    if any(term in text for term in ["sem álcool", "sem alcool", "sem alcohol denat"]):
        excluded.add("alcohol denat")
    if "sem óleo" in text or "sem oleo" in text:
        excluded.update({"mineral oil", "shea butter"})
    return sorted(excluded)


def detect_goal_from_message(message: str) -> str | None:
    text = message.lower()
    if any(term in text for term in ["acne", "espinha", "espinhas", "cravo", "cravos"]):
        return "acne"
    if any(term in text for term in ["oleosidade", "pele oleosa", "oleosa"]):
        return "oil_control"
    if any(term in text for term in ["barreira", "sensibilizada", "ardendo", "sensivel", "sensível"]):
        return "barrier"
    if any(term in text for term in ["manchas", "melasma"]):
        return "hyperpigmentation"
    if any(term in text for term in ["textura", "poros"]):
        return "texture"
    if any(term in text for term in ["anti-idade", "rugas"]):
        return "anti_aging"
    return None


def extract_explicit_user_preferences(message: str) -> dict:
    text = message.lower()
    tolerated: set[str] = set()
    triggers: set[str] = set()
    positive_terms = ["funcionou bem", "ficou otima", "ficou ótima", "tolero bem", "deu certo", "minha pele gostou"]
    trigger_terms = ["arde", "ardeu", "irrita", "irritou", "resseca", "ressecou", "piora", "me da acne", "me dá acne"]
    chunks = [chunk.strip() for chunk in text.replace("\n", ".").replace(" mas ", ".").replace(" e ", ".").split(".") if chunk.strip()]

    for ingredient in PREFERENCE_INGREDIENTS:
        for chunk in chunks:
            if ingredient not in chunk:
                continue
            nearby_positive = any(term in chunk for term in positive_terms)
            nearby_trigger = any(term in chunk for term in trigger_terms)
            if nearby_positive and ingredient not in {"fragrance", "parfum", "perfume", "alcohol denat"}:
                tolerated.add(ingredient)
            if nearby_trigger:
                if ingredient in {"parfum", "perfume"}:
                    triggers.add("fragrance")
                else:
                    triggers.add(ingredient)

    if any(term in text for term in ["sem fragrância", "sem fragrancia", "sem perfume", "sem parfum"]):
        triggers.add("fragrance")

    constraints: dict = {}
    category = detect_product_category_request(message)
    price = detect_price_constraint(message)
    if category:
        constraints["preferred_category"] = category
    if price:
        constraints["price_range"] = price

    return {
        "explicit_tolerated_ingredients": sorted(tolerated),
        "explicit_trigger_ingredients": sorted(triggers),
        "explicit_goals": [goal for goal in [detect_goal_from_message(message)] if goal],
        "explicit_constraints": constraints,
    }


def build_recommendation_constraints_from_message(message: str, user_context: dict | None = None) -> dict:
    context = user_context or {}
    explicit = extract_explicit_user_preferences(message)
    category = detect_product_category_request(message)
    price = detect_price_constraint(message)
    excluded = set(detect_excluded_ingredients(message)) | set(explicit["explicit_trigger_ingredients"])

    for trigger in context.get("known_triggers", []) or []:
        if str(trigger).strip().lower() in {"fragrance", "parfum", "perfume", "alcohol denat"}:
            excluded.add(str(trigger).strip().lower())

    affinity = context.get("ingredient_affinity", {}) or {}
    for item in affinity.get("problematic", []) or []:
        if float(item.get("confidence", 0) or 0) >= 0.75:
            excluded.add(str(item.get("ingredient_name", "")).strip().lower())

    text = message.lower()
    max_irritation = None
    if any(term in text for term in ["mais seguro", "mais segura"]):
        max_irritation = 50
    elif any(term in text for term in ["sensivel", "sensível", "pele sensível", "pele sensivel"]):
        max_irritation = 60

    return {
        "main_goal": detect_goal_from_message(message) or "general",
        "exclude_ingredients": sorted(item for item in excluded if item),
        "constraints": {
            "price_range": price,
            "preferred_category": category,
            "routine_step_needed": category if category in {"sunscreen", "cleanser", "moisturizer"} else None,
            "max_irritation_risk": max_irritation,
            "avoid_active_treatments": any(term in text for term in ["sem ativo", "sem acido", "sem ácido"]),
            "explicit_tolerated_ingredients": explicit["explicit_tolerated_ingredients"],
            "explicit_trigger_ingredients": sorted(item for item in set(explicit["explicit_trigger_ingredients"]) | excluded if item),
            "explicit_goals": explicit["explicit_goals"],
        },
    }


def detect_ingredient_explanation_intent(message: str) -> bool:
    text = message.lower()
    if detect_reaction_intent(message):
        return False
    return any(term in text for term in ["o que", "pra que", "para que", "ingrediente", "faz?"]) and any(
        marker in text for marker in INCI_MARKERS
    )


def extract_inci_from_message(message: str) -> str | None:
    normalized = message.replace("\n", " ")
    lower = normalized.lower()
    marker_positions = [lower.find(marker) for marker in INCI_MARKERS if lower.find(marker) != -1]
    if not marker_positions or "," not in normalized:
        return None

    start = max(0, min(marker_positions))
    end = len(normalized)
    for token in [" o que ", " minha pele ", " depois ", " usei ", " usei esse ", " agora quero", " mas ", "?"]:
        position = lower.find(token, start)
        if position != -1 and position > start:
            end = min(end, position)
    formula = normalized[start:end].strip(" :;.? \t")
    parts = [part.strip(" .") for part in formula.split(",") if part.strip(" .")]
    if len(parts) < 2:
        return None
    return ", ".join(parts)


def plan_agent_response(request: AgentChatRequest, agent_context: dict) -> AgentPlan:
    text = request.message.lower()
    message_has_formula = extract_inci_from_message(request.message) is not None
    context_has_formula = bool(request.context.raw_ingredient_list)
    has_formula = context_has_formula or message_has_formula
    context_status = agent_context.get("context_status")
    missing_info: list[str] = []

    if detect_safety_urgent(request.message):
        return AgentPlan(intent=AgentIntent.unknown, confidence="high", risk_level="high")

    recommendation_payload = build_recommendation_constraints_from_message(request.message, agent_context)
    is_recommendation = detect_recommendation_intent(request.message)
    is_specific_analysis = detect_specific_product_analysis_intent(
        request.message,
        request.context.raw_ingredient_list,
    )

    reaction_intent = detect_reaction_intent(request.message)

    if is_recommendation and not message_has_formula and (not reaction_intent or detect_forward_recommendation_request(request.message)):
        return AgentPlan(
            intent=AgentIntent.recommend_products,
            confidence="high" if context_status != "insufficient_history" else "medium",
            tools_needed=["recommend_products"],
            recommendation_payload=recommendation_payload,
            answer_strategy="recommend_ranked_products_with_personalization",
            risk_level="low",
        )

    if reaction_intent:
        tools = ["get_personal_insights", "get_analysis_history"]
        if has_formula:
            tools.insert(0, "analyze_product")
        else:
            missing_info.append("raw_ingredient_list")
        return AgentPlan(
            intent=AgentIntent.explain_reaction,
            confidence="high" if not missing_info else "low",
            missing_info=missing_info,
            tools_needed=tools,
            should_ask_clarifying_question=not has_formula,
            clarifying_question="Pode colar a formula INCI completa ou enviar uma foto do rotulo?",
            answer_strategy="Relacionar reacao com historico, possiveis ingredientes suspeitos e acao de pausa.",
            risk_level="medium",
        )

    if message_has_formula or is_specific_analysis:
        return AgentPlan(
            intent=AgentIntent.analyze_product,
            confidence="high",
            tools_needed=["analyze_product"],
            answer_strategy="Dar veredito direto, score real, motivos, pontos de atencao e proximo passo.",
            risk_level="low",
        )

    if any(term in text for term in ["comparar", "compare", "versus", " vs "]):
        missing_info.append("formula_dos_produtos")
        return AgentPlan(
            intent=AgentIntent.compare_products,
            confidence="medium",
            missing_info=missing_info,
            should_ask_clarifying_question=True,
            clarifying_question="Pode me enviar a formula INCI dos produtos que voce quer comparar?",
            answer_strategy="Comparar score, riscos e pontos de atencao reais.",
            risk_level="low",
        )

    if detect_recommendation_intent(request.message):
        return AgentPlan(
            intent=AgentIntent.recommend_products,
            confidence="high" if context_status != "insufficient_history" else "medium",
            tools_needed=["recommend_products"],
            recommendation_payload=recommendation_payload,
            answer_strategy="recommend_ranked_products_with_personalization",
            risk_level="low",
        )

    if detect_routine_intent(request.message):
        intent = AgentIntent.adjust_routine if any(term in text for term in ["melhorar", "ajustar", "trocar"]) else AgentIntent.generate_routine
        return AgentPlan(
            intent=intent,
            confidence="high",
            tools_needed=["generate_routine"] if intent == AgentIntent.generate_routine else ["get_current_routine", "adjust_routine"],
            answer_strategy="Montar rotina com passos completos, frequencia, cuidados e um proximo passo.",
            risk_level="low",
        )

    if detect_ingredient_explanation_intent(request.message):
        return AgentPlan(
            intent=AgentIntent.explain_ingredients,
            confidence="medium",
            tools_needed=["get_personal_insights"],
            answer_strategy="Explicar funcao, perfil ideal, cautelas e uso seguro com base em insights.",
            risk_level="low",
        )

    if any(term in text for term in ["historico", "histórico", "gatilho", "toler", "insight"]):
        return AgentPlan(
            intent=AgentIntent.get_personal_insights,
            confidence="high",
            tools_needed=["get_personal_insights"],
            answer_strategy="Resumir gatilhos, tolerados, limitacoes e proximo feedback util.",
            risk_level="low",
        )

    if context_has_formula and any(term in text for term in ["produto", "formula", "fórmula", "acne", "cravo", "serum", "sérum", "bom para mim"]):
        return AgentPlan(
            intent=AgentIntent.analyze_product,
            confidence="low",
            tools_needed=["analyze_product"],
            answer_strategy="Dar veredito direto, score real, motivos, pontos de atencao e proximo passo.",
            risk_level="low",
        )

    if any(term in text for term in ["produto", "formula", "fórmula", "serum", "sérum", "bom para mim"]):
        return AgentPlan(
            intent=AgentIntent.analyze_product,
            confidence="low",
            missing_info=["raw_ingredient_list"],
            should_ask_clarifying_question=True,
            clarifying_question="Pode colar a lista INCI completa ou enviar uma foto do rotulo?",
            answer_strategy="Pedir formula antes de analisar, sem inventar score.",
            risk_level="low",
        )

    return AgentPlan(
        intent=AgentIntent.general_question,
        confidence="low",
        should_ask_clarifying_question=True,
        clarifying_question="Voce quer analisar um produto, montar rotina ou investigar uma reacao?",
        answer_strategy="Perguntar uma coisa so para direcionar a ferramenta certa.",
        risk_level="low",
    )
