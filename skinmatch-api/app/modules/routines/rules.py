from app.modules.skin_profiles.schemas import SkinProfileInput


STRONG_ACTIVES = {"retinol", "retinal", "glycolic acid", "lactic acid", "salicylic acid", "benzoyl peroxide"}
AHA_BHA = {"glycolic acid", "lactic acid", "salicylic acid"}
HEAVY_OILS = {"mineral oil", "shea butter"}


def normalized(values: list[str]) -> set[str]:
    return {value.strip().lower().removesuffix(".") for value in values if value.strip()}


def infer_product_type(product_analysis: dict) -> str:
    ingredients = normalized(product_analysis.get("ingredient_names", []))
    name = str(product_analysis.get("name", "")).lower()
    routine_step = str(product_analysis.get("routine_step") or "").lower()
    category = str(product_analysis.get("category") or "").lower()

    if routine_step in {"cleanser", "toner", "treatment", "moisturizer", "sunscreen"}:
        return routine_step
    if product_analysis.get("is_sunscreen") or category == "sunscreen":
        return "sunscreen"
    if product_analysis.get("is_cleanser") or category == "cleanser":
        return "cleanser"
    if product_analysis.get("is_moisturizer") or category in {"moisturizer", "barrier_repair"}:
        return "moisturizer"
    if product_analysis.get("is_active_treatment") or category in {"acne_treatment", "treatment"}:
        return "treatment"

    if "sunscreen" in name or "spf" in name or "uv filter" in ingredients or "zinc oxide" in ingredients:
        return "sunscreen"
    if "cleanser" in name or "gel de limpeza" in name or "limpador" in name:
        return "cleanser"
    if "toner" in name or "tonico" in name:
        return "toner"
    if ingredients & {"salicylic acid", "azelaic acid", "benzoyl peroxide", "retinol", "retinal", "glycolic acid", "lactic acid", "niacinamide"}:
        return "treatment"
    if ingredients & {"ceramide", "panthenol", "glycerin", "hyaluronic acid", "shea butter", "mineral oil"}:
        return "moisturizer"
    return "treatment"


def has_conflicting_actives(products: list[dict]) -> bool:
    ingredients = set()
    for product in products:
        ingredients.update(normalized(product.get("ingredient_names", [])))
    return bool({"retinol", "retinal"} & ingredients and AHA_BHA & ingredients)


def strong_active_count(products: list[dict]) -> int:
    ingredients = set()
    for product in products:
        ingredients.update(normalized(product.get("ingredient_names", [])))
    return len(ingredients & STRONG_ACTIVES)


def routine_order(period: str) -> list[str]:
    if period == "morning":
        return ["cleanser", "treatment", "moisturizer", "sunscreen"]
    return ["cleanser", "treatment", "moisturizer"]


def generate_step_instructions(step_type: str, product: dict, skin_profile: SkinProfileInput) -> str:
    if step_type == "cleanser":
        return "Use uma pequena quantidade e enxague com agua morna."
    if step_type == "treatment":
        if skin_profile.sensitive_skin:
            return "Aplique em pequena quantidade em noites alternadas e observe a resposta da pele."
        return "Aplique em pequena quantidade e observe a resposta da pele."
    if step_type == "moisturizer":
        return "Aplique uma camada fina para ajudar a manter a barreira da pele."
    if step_type == "sunscreen":
        return "Aplique generosamente pela manha e reaplique ao longo do dia."
    if step_type == "toner":
        return "Aplique suavemente, evitando excesso de friccao."
    return "Introduza gradualmente e observe sinais de irritacao."


def generate_step_reason(step_type: str, product: dict, skin_profile: SkinProfileInput, main_goal: str) -> str:
    ingredients = normalized(product.get("ingredient_names", []))
    if step_type == "cleanser":
        return "Ajuda a remover oleosidade e residuos sem adicionar muitos ativos."
    if step_type == "sunscreen":
        return "Protecao solar pela manha reduz risco de sensibilizacao e manchas."
    if main_goal == "acne" and ingredients & {"salicylic acid", "niacinamide", "azelaic acid"}:
        return "Ajuda no controle da acne com ativos relevantes para o objetivo."
    if step_type == "moisturizer" and ingredients & {"ceramide", "panthenol", "glycerin", "hyaluronic acid"}:
        return "Ajuda a reforcar a barreira e reduzir ressecamento."
    if ingredients & normalized(skin_profile.tolerated_ingredients):
        return "Inclui ingredientes que sua pele costuma tolerar bem."
    return "Foi selecionado por compatibilidade e menor risco relativo."


def routine_warnings(morning_products: list[dict], night_products: list[dict], skin_profile: SkinProfileInput) -> list[str]:
    warnings = [
        "Introduza novos produtos gradualmente.",
        "Faca teste de contato antes de usar uma rotina nova no rosto todo.",
    ]
    if has_conflicting_actives(morning_products) or has_conflicting_actives(night_products):
        warnings.append("Evite usar acidos fortes e retinol na mesma rotina.")
    if strong_active_count(morning_products + night_products) >= 2:
        warnings.append("Evite iniciar varios ativos fortes ao mesmo tempo.")
    if skin_profile.sensitive_skin:
        warnings.append("Como sua pele foi marcada como sensivel, comece com menos frequencia e observe sinais de irritacao.")
    return warnings
