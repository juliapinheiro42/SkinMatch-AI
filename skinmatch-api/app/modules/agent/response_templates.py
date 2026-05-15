from typing import Any

from app.modules.agent.schemas import EDUCATIONAL_DISCLAIMER, AgentIntent


INGREDIENT_SYNONYMS = {
    "fragrance": "Fragrance (parfum)",
    "parfum": "Fragrance (parfum)",
    "perfume": "Fragrance (parfum)",
    "alcohol denat": "Alcohol denat.",
    "alcohol denat.": "Alcohol denat.",
    "salicylic acid": "Salicylic acid",
}


def _join(items: list[str], fallback: str) -> str:
    clean = []
    seen = set()
    for item in items:
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            clean.append(value)
            seen.add(key)
    return ", ".join(clean[:5]) if clean else fallback


def _ingredient_label(value: str) -> str:
    normalized = str(value).strip().lower().removesuffix(".")
    return INGREDIENT_SYNONYMS.get(normalized, str(value).strip())


def _dedupe(items: list[str]) -> list[str]:
    clean = []
    seen = set()
    for item in items:
        value = _ingredient_label(str(item))
        key = value.lower()
        if value and key not in seen:
            clean.append(value)
            seen.add(key)
    return clean


def _risk_text(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "risco de irritacao estimado: nao disponivel."

    if number <= 1:
        number *= 100
    number = max(0, min(100, round(number)))
    if number < 35:
        return "risco de irritacao estimado: baixo."
    if number < 70:
        return "risco de irritacao estimado: moderado."
    return "risco de irritacao estimado: alto."


def _history_text(insights: dict[str, Any]) -> str:
    triggers = [_ingredient_label(item.get("ingredient")) for item in insights.get("common_triggers", []) if item.get("ingredient")]
    if triggers:
        return f"No seu historico, {_join(triggers, 'alguns ingredientes')} aparece como possivel gatilho."
    return "Ainda nao ha feedbacks suficientes no seu historico para confirmar um padrao pessoal."


def _skin_profile_text(agent_context: dict) -> str:
    profile = agent_context.get("skin_profile") or {}
    details = []
    if profile.get("skin_type") == "oily":
        details.append("oleosa")
    if profile.get("sensitive_skin"):
        details.append("sensivel")
    if profile.get("acne_prone"):
        details.append("com tendencia a acne")
    if profile.get("barrier_compromised"):
        details.append("com barreira fragilizada")
    return "como sua pele e " + ", ".join(details) if details else "considerando o perfil informado"


def _prioritize_suspects(suspicious: list[str], agent_context: dict) -> tuple[str, list[str]]:
    known = {_ingredient_label(item).lower() for item in agent_context.get("known_triggers", [])}
    for item in suspicious:
        if item.lower() in known:
            return item, [candidate for candidate in suspicious if candidate != item]
    for preferred in ["Fragrance (parfum)", "Alcohol denat.", "Salicylic acid"]:
        if preferred in suspicious:
            return preferred, [candidate for candidate in suspicious if candidate != preferred]
    if suspicious:
        return suspicious[0], suspicious[1:]
    return "nenhum ingrediente isolado", []


def _next_step(intent: AgentIntent) -> str:
    suggestions = {
        AgentIntent.analyze_product: "Quer que eu compare com alternativas mais seguras?",
        AgentIntent.recommend_products: "Minha sugestao e comecar pela primeira opcao e observar a pele por alguns dias.",
        AgentIntent.generate_routine: "Quer que eu monte uma versao mais minimalista?",
        AgentIntent.explain_reaction: "Quer que eu te ajude a identificar o produto mais suspeito da rotina?",
        AgentIntent.adjust_routine: "Quer que eu transforme isso em uma rotina de 3 passos?",
        AgentIntent.get_personal_insights: "O proximo passo mais util e registrar feedback depois de usar um produto.",
    }
    return suggestions.get(intent, "O proximo passo e me enviar uma formula ou objetivo especifico.")


def follow_up_for_intent(intent: AgentIntent) -> str | None:
    return _next_step(intent)


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
        return f"Nao encontrei uma rotina estruturada para exibir.\n\n{EDUCATIONAL_DISCLAIMER}"

    morning = routine_result.get("morning_routine") or []
    night = routine_result.get("night_routine") or []
    warnings = routine_result.get("warnings") or []
    has_any_step = bool(morning or night)
    sections = [
        _format_routine_section("🌞 Rotina da manhã", "Nenhuma etapa encontrada para manhã.", morning),
        _format_routine_section("🌙 Rotina da noite", "Nenhuma etapa encontrada para noite.", night),
        "⚠️ Cuidados",
    ]
    sections.extend(f"- {warning}" for warning in warnings) if warnings else sections.append("- Introduza novos produtos gradualmente.")
    if not has_any_step:
        sections.extend(["", "Nao encontrei produtos suficientes no catalogo para montar uma rotina completa com os filtros atuais."])
    sections.extend(["", EDUCATIONAL_DISCLAIMER])
    return "\n\n".join(sections)


def render_analyze_product(result: dict[str, Any], agent_context: dict) -> str:
    positives = _join(result.get("positive_ingredients", []), "nenhum ponto positivo forte identificado")
    warnings = _join(result.get("warning_ingredients", []), "nenhum alerta principal identificado")
    triggers = _join(agent_context.get("known_triggers", []), "sem gatilhos pessoais suficientes no historico")
    affinity = agent_context.get("ingredient_affinity") or {}
    problematic = _join(
        [item.get("ingredient_name", "") for item in affinity.get("problematic", [])],
        "nenhum ingrediente com tolerancia negativa relevante",
    )
    return (
        f"Veredito direto: o produto ficou como {result.get('verdict')} com score {result.get('compatibility_score')}.\n\n"
        f"Por que pode funcionar: {positives} podem ajudar no objetivo informado.\n\n"
        f"Pontos de atencao: {warnings}. Considerando seu historico, gatilhos conhecidos: {triggers}. "
        f"Afinidade aprendida: {problematic}.\n\n"
        "Como introduzir com seguranca: faca teste de contato e use em dias alternados no inicio, especialmente se houver ardor ou ressecamento.\n\n"
        f"Proximo passo: {_next_step(AgentIntent.analyze_product)}\n\n"
        f"{EDUCATIONAL_DISCLAIMER}"
    )


def render_recommend_products(results: list[dict[str, Any]], agent_context: dict) -> str:
    if not results:
        return (
            "Nao encontrei produtos suficientes no catalogo para recomendar com seguranca. "
            "Voce pode cadastrar mais produtos ou remover alguns filtros.\n\n"
            f"Proximo passo: {_next_step(AgentIntent.recommend_products)}\n\n"
            f"{EDUCATIONAL_DISCLAIMER}"
        )
    affinity = agent_context.get("ingredient_affinity") or {}
    recommendation_payload = agent_context.get("recommendation_payload") or {}
    recommendation_constraints = recommendation_payload.get("constraints") or {}
    tolerated_affinity = [
        str(item.get("ingredient_name"))
        for item in affinity.get("well_tolerated", [])
        if item.get("ingredient_name")
    ]
    problematic_affinity = [
        str(item.get("ingredient_name"))
        for item in affinity.get("problematic", [])
        if item.get("ingredient_name")
    ]
    avoid_items = agent_context.get("known_triggers", []) + problematic_affinity
    avoid_items += recommendation_payload.get("exclude_ingredients", []) + recommendation_constraints.get("explicit_trigger_ingredients", [])
    tolerated_items = (
        agent_context.get("tolerated_ingredients", [])
        + tolerated_affinity
        + recommendation_constraints.get("explicit_tolerated_ingredients", [])
    )
    goal = recommendation_payload.get("main_goal") or ", ".join(agent_context.get("user_goals", [])[:2]) or "o objetivo informado"
    category = recommendation_constraints.get("preferred_category") or "produto"
    price = recommendation_constraints.get("price_range")
    profile = agent_context.get("skin_profile") or {}
    profile_bits = []
    if profile.get("skin_type") == "oily":
        profile_bits.append("oleosa")
    if profile.get("sensitive_skin"):
        profile_bits.append("sensivel")
    if profile.get("acne_prone"):
        profile_bits.append("com tendencia a acne")
    profile_text = ", ".join(profile_bits) or "o perfil informado"
    criteria = [f"buscar {category}"]
    if avoid_items:
        criteria.append(f"evitar {_join(avoid_items, 'gatilhos')}")
    if tolerated_items:
        criteria.append(f"priorizar {_join(tolerated_items, 'ingredientes tolerados')}")
    if price:
        criteria.append(f"manter faixa {price}")
    lines = [
        f"Como sua pele e {profile_text}, eu priorizei {category}s leves, sem seus gatilhos principais e com baixo risco de irritacao.",
        "",
        f"Usei como criterios: {', '.join(criteria)}.",
        "",
        "Recomendacoes:",
    ]
    for index, item in enumerate(results[:5], start=1):
        keys = _join(item.get("key_ingredients", []), "sem ingrediente-chave destacado")
        score = item.get("final_score", item.get("compatibility_score"))
        lines.append(
            f"{index}. {item.get('brand')} {item.get('name')} ({item.get('category') or category})\n"
            f"   Score: {score}\n"
            f"   Por que foi recomendado: {item.get('reason')}.\n"
            f"   Ingredientes-chave: {keys}."
        )
    avoid = _join(avoid_items, "sem gatilhos pessoais suficientes no historico")
    tolerated = _join(tolerated_items, "ainda sem ingredientes bem tolerados recorrentes")
    lines.extend(
        [
            "",
            "Personalizacao:",
            f"- Objetivo principal: {goal}.",
            f"- Sua pele parece tolerar bem: {tolerated}.",
            f"- Ingredientes a evitar: {avoid}.",
            f"Melhor opcao para comecar: {results[0].get('brand')} {results[0].get('name')}, porque {str(results[0].get('reason', '')).removesuffix('.')}.",
            "Limitacao: essa recomendacao depende dos produtos cadastrados no catalogo.",
            "Proximo passo: Quer que eu monte uma rotina usando essas opcoes?",
            "",
            EDUCATIONAL_DISCLAIMER,
        ]
    )
    return "\n".join(lines)


def render_explain_reaction(results: dict[str, Any], agent_context: dict) -> str:
    analysis = results.get("analysis")
    insights = results.get("insights", {})
    history = results.get("history", [])
    suspicious = []
    if isinstance(analysis, dict):
        suspicious.extend(analysis.get("warning_ingredients", []))
        suspicious.extend(
            ingredient
            for ingredient in ["fragrance", "parfum", "alcohol denat", "salicylic acid"]
            if ingredient in str(analysis).lower()
        )
    suspicious.extend(item.get("ingredient") for item in insights.get("common_triggers", [])[:3])
    suspicious = _dedupe([item for item in suspicious if item])
    explanation_mentions = ["fragrance", "parfum", "alcohol denat", "salicylic acid"]
    for ingredient in explanation_mentions:
        label = _ingredient_label(ingredient)
        if label.lower() not in {item.lower() for item in suspicious}:
            suspicious.append(label)
    main_suspect, other_suspects = _prioritize_suspects(suspicious, agent_context)
    suspicious_text = (
        f"principal suspeito: {main_suspect}. "
        f"Outros possiveis: {_join(other_suspects, 'nenhum outro suspeito claro')}."
    )
    recent = _history_text(insights)
    profile_text = _skin_profile_text(agent_context)
    risk = ""
    if isinstance(analysis, dict):
        risk = (
            f" A analise indicou {_risk_text(analysis.get('irritation_risk'))} "
            f"Veredito: {analysis.get('verdict')}."
        )
    return (
        f"Resposta direta: {profile_text}, a ardencia e as espinhas podem indicar baixa tolerancia a essa combinacao da formula.\n\n"
        f"Causas provaveis: {suspicious_text}\n\n"
        f"Por que faz sentido: Salicylic acid pode ajudar acne, mas tambem aumenta chance de ardor quando vem junto de Alcohol denat. e Fragrance (parfum). Essa combinacao pode ser mais dificil para pele sensivel, especialmente se fragrancia ja foi um problema para voce.{risk} {recent}\n\n"
        "Acao agora: pause temporariamente esse produto. Mantenha por alguns dias uma rotina simples: limpeza suave, hidratante e protetor solar. Evite outros acidos, retinol e produtos perfumados ate a pele acalmar.\n\n"
        "Cuidados: se houver dor intensa, inchaco, ferida, queimadura forte ou falta de ar, procure atendimento medico.\n\n"
        f"Proximo passo: {_next_step(AgentIntent.explain_reaction)}\n\n"
        f"{EDUCATIONAL_DISCLAIMER}"
    )


def render_personal_insights(result: dict[str, Any], agent_context: dict) -> str:
    if agent_context.get("context_status") == "insufficient_history":
        return (
            "Ainda tenho poucos dados do seu historico, entao nao vou fingir uma personalizacao forte.\n\n"
            "Acao recomendada: registre feedback depois de usar produtos por alguns dias para eu identificar gatilhos e ingredientes bem tolerados.\n\n"
            f"{EDUCATIONAL_DISCLAIMER}"
        )
    triggers = _join([item["ingredient"] for item in result.get("common_triggers", [])[:5]], "nenhum gatilho recorrente")
    tolerated = _join([item["ingredient"] for item in result.get("well_tolerated_ingredients", [])[:5]], "nenhum tolerado recorrente")
    patterns = " ".join(result.get("patterns", [])[:2]) or "Ainda nao ha padroes fortes."
    return (
        f"Baseado no seu historico: possiveis gatilhos incluem {triggers}.\n\n"
        f"Ingredientes bem tolerados: {tolerated}.\n\n"
        f"Padroes detectados: {patterns}\n\n"
        f"Proximo passo: {_next_step(AgentIntent.get_personal_insights)}\n\n"
        f"{EDUCATIONAL_DISCLAIMER}"
    )


def render_adjust_routine(result: dict[str, Any], agent_context: dict) -> str:
    return (
        "O que manter: limpeza suave, hidratante de barreira e protetor solar.\n\n"
        "O que pausar: ativos fortes se houve ardor, ressecamento ou vermelhidao recente.\n\n"
        "O que trocar: priorize produtos com menor risco e sem seus gatilhos pessoais.\n\n"
        f"Nova rotina sugerida:\n{format_routine_result(result)}\n\n"
        "Como acompanhar evolucao: registre irritacao, acne, ressecamento e satisfacao apos alguns dias de uso."
    )


def render_explain_ingredients(agent_context: dict) -> str:
    limitation = (
        "Tenho poucos dados do seu historico, entao nao vou fingir personalizacao forte.\n\n"
        if agent_context.get("context_status") == "insufficient_history"
        else ""
    )
    triggers = _join(agent_context.get("known_triggers", []), "nenhum gatilho pessoal recorrente")
    tolerated = _join(agent_context.get("tolerated_ingredients", []), "nenhum ingrediente tolerado recorrente")
    return (
        f"{limitation}"
        "O que o ingrediente faz: depende do ingrediente especifico, mas eu posso avaliar funcao, risco e beneficio quando voce me disser qual e.\n\n"
        f"Para seu contexto: gatilhos registrados incluem {triggers}; ingredientes tolerados incluem {tolerated}.\n\n"
        "Quando pode ser ruim: se ja apareceu associado a ardor, acne, ressecamento ou irritacao nos seus feedbacks.\n\n"
        "Como usar com seguranca: introduza um ingrediente ativo por vez.\n\n"
        f"Proximo passo: envie o nome do ingrediente ou a formula completa.\n\n{EDUCATIONAL_DISCLAIMER}"
    )


def render_template(intent: AgentIntent, structured_result: Any, agent_context: dict) -> str:
    if intent == AgentIntent.analyze_product and isinstance(structured_result, dict):
        return render_analyze_product(structured_result, agent_context)
    if intent == AgentIntent.recommend_products and isinstance(structured_result, list):
        return render_recommend_products(structured_result, agent_context)
    if intent == AgentIntent.generate_routine and isinstance(structured_result, dict):
        return format_routine_result(structured_result)
    if intent == AgentIntent.explain_reaction and isinstance(structured_result, dict):
        return render_explain_reaction(structured_result, agent_context)
    if intent == AgentIntent.adjust_routine and isinstance(structured_result, dict):
        return render_adjust_routine(structured_result, agent_context)
    if intent == AgentIntent.get_personal_insights and isinstance(structured_result, dict):
        return render_personal_insights(structured_result, agent_context)
    if intent == AgentIntent.explain_ingredients:
        return render_explain_ingredients(agent_context)
    return (
        "Consigo te ajudar melhor se voce me disser se quer analisar um produto, montar uma rotina ou investigar uma reacao.\n\n"
        f"Proximo passo: envie uma formula INCI, uma foto do rotulo ou seu objetivo principal.\n\n{EDUCATIONAL_DISCLAIMER}"
    )
