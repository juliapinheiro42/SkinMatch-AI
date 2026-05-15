from typing import Any

from app.modules.agent.schemas import EDUCATIONAL_DISCLAIMER, AgentIntent


DIAGNOSIS_TERMS = ["voce tem dermatite", "voce tem rosacea", "diagnostico", "diagnóstico"]
PRACTICAL_TERMS = [
    "proximo passo",
    "ação recomendada",
    "acao recomendada",
    "pause",
    "use ",
    "envie",
    "registre",
    "comece",
    "introduza",
]
TOOL_REQUIRED = {
    AgentIntent.analyze_product,
    AgentIntent.recommend_products,
    AgentIntent.generate_routine,
    AgentIntent.explain_reaction,
    AgentIntent.adjust_routine,
    AgentIntent.get_personal_insights,
}


def validate_agent_response(
    response: str,
    *,
    intent: AgentIntent,
    tools_used: list[str],
    structured_result: Any | None,
    confidence: str,
) -> list[str]:
    failures: list[str] = []
    lower = response.lower()
    if EDUCATIONAL_DISCLAIMER not in response:
        failures.append("missing_disclaimer")
    if any(term in lower for term in DIAGNOSIS_TERMS):
        failures.append("diagnosis_language")
    if "score" in lower and structured_result is None:
        failures.append("invented_score_without_structured_result")
    if not any(term in lower for term in PRACTICAL_TERMS):
        failures.append("missing_practical_next_step")
    if intent in TOOL_REQUIRED and not tools_used:
        failures.append("missing_required_tool")
    if confidence == "low" and not any(term in lower for term in ["poucos dados", "limitação", "limitacao", "preciso"]):
        failures.append("missing_low_confidence_limitation")
    if intent == AgentIntent.explain_reaction:
        if not any(term in lower for term in ["possiveis causas", "resposta direta", "pode estar relacionado"]):
            failures.append("missing_reaction_cause")
        if not any(term in lower for term in ["pause", "pausar", "simplifique", "evite"]):
            failures.append("missing_reaction_action")
        if not any(term in lower for term in ["procure atendimento", "procurar ajuda", "ajuda medica", "atendimento medico"]):
            failures.append("missing_reaction_safety")
        if "analyze_product" in tools_used and "analysis" not in str(structured_result):
            failures.append("missing_analysis_result_for_reaction")
    return failures


def safe_fallback(intent: AgentIntent, confidence: str) -> str:
    limitation = "Tenho poucos dados para personalizar com seguranca. " if confidence == "low" else ""
    return (
        f"{limitation}Para evitar uma resposta generica ou inventada, preciso de mais contexto antes de concluir.\n\n"
        "Proximo passo: envie a formula INCI, seu objetivo principal ou o feedback de uso do produto.\n\n"
        f"{EDUCATIONAL_DISCLAIMER}"
    )
