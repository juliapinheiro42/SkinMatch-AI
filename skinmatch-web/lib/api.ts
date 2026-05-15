import type {
  AnalysisRequest,
  AnalysisResponse,
  AgentChatRequest,
  AgentChatResponse,
  CatalogProduct,
  CatalogProductFilters,
  AnalysisDetail,
  AnalysisHistoryItem,
  AppliedRule,
  IngredientReason,
  PersonalInsightsResponse,
  ProductFeedbackRequest,
  ProductFeedbackResponse,
  OcrFormulaResponse,
  RecommendationItem,
  RecommendationRequest,
  RoutineResponse,
  SimilarProduct,
  Verdict,
} from "@/types/analysis";

type BackendAnalysisResponse = {
  analysis_id: string;
  product_id: string;
  compatibility_score: number;
  verdict: string;
  irritation_risk: number;
  acne_risk: number;
  benefit_score: number;
  applied_rules: string[];
  positive_ingredients: string[];
  warning_ingredients: string[];
  unknown_ingredients: string[];
  recommendation: string;
  disclaimer: string;
};

type BackendAnalysisDetail = Omit<BackendAnalysisResponse, "parsed_ingredients"> & {
  product_name?: string | null;
  brand?: string | null;
  main_goal: string;
  raw_ingredient_list: string;
  skin_profile_snapshot: AnalysisRequest["skin_profile"];
  parsed_formula_snapshot: Array<{
    position: number;
    raw_name: string;
    normalized_name: string;
    inci_name: string;
    unknown: boolean;
    concentration_band: string;
  }>;
  barrier_support: number;
  created_at: string;
  feedback?: ProductFeedbackResponse | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ruleLabels: Record<string, string> = {
  RULE_001: "Fragrancia pode elevar cautela em pele sensivel.",
  RULE_002: "Alcohol denat tende a exigir cautela quando a barreira esta comprometida.",
  RULE_003: "Salicylic acid pode favorecer perfis acneicos.",
  RULE_004: "Retinol com glycolic acid pode aumentar chance de irritacao.",
  RULE_005: "A formula contem ingrediente informado como gatilho.",
  RULE_006: "Ingrediente tolerado reduz a estimativa de risco.",
  RULE_007: "Ingredientes de suporte de barreira podem melhorar a compatibilidade.",
  RULE_008: "Historico pessoal sugere possivel gatilho para este ingrediente.",
  RULE_009: "Historico pessoal sugere boa tolerancia a este ingrediente.",
};

function toPercent(value: number): number {
  const percent = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(percent)));
}

function normalizeVerdict(value: string, score: number): Verdict {
  if (value === "good_match" || value === "caution" || value === "high_risk") {
    return value;
  }

  if (value === "highly compatible" || score >= 80) {
    return "good_match";
  }

  if (value === "low compatibility" || score < 60) {
    return "high_risk";
  }

  return "caution";
}

function ingredientReasons(items: string[], kind: "positive" | "warning"): IngredientReason[] {
  return items.map((name) => ({
    name,
    reason:
      kind === "positive"
        ? "Pode contribuir positivamente com base no perfil informado."
        : "Pode merecer atencao conforme sensibilidade, concentracao estimada ou historico informado.",
  }));
}

function appliedRules(items: string[]): AppliedRule[] {
  return items.map((code) => ({
    code,
    label: ruleLabels[code] ?? "Regra deterministica aplicada na estimativa.",
  }));
}

function normalizeResponse(response: BackendAnalysisResponse): AnalysisResponse {
  const compatibilityScore = toPercent(response.compatibility_score);

  return {
    analysis_id: response.analysis_id,
    product_id: response.product_id,
    compatibility_score: compatibilityScore,
    verdict: normalizeVerdict(response.verdict, compatibilityScore),
    irritation_risk: toPercent(response.irritation_risk),
    acne_risk: toPercent(response.acne_risk),
    benefit_score: toPercent(response.benefit_score),
    applied_rules: appliedRules(response.applied_rules ?? []),
    positive_ingredients: ingredientReasons(response.positive_ingredients ?? [], "positive"),
    warning_ingredients: ingredientReasons(response.warning_ingredients ?? [], "warning"),
    unknown_ingredients: response.unknown_ingredients ?? [],
    recommendation:
      response.recommendation ||
      "Use esta estimativa como ponto de partida e observe como sua pele tende a responder.",
    disclaimer:
      response.disclaimer ||
      "Esta analise e uma estimativa educacional e nao substitui orientacao medica ou dermatologica.",
  };
}

function normalizeDetail(response: BackendAnalysisDetail): AnalysisDetail {
  const compatibilityScore = toPercent(response.compatibility_score);

  return {
    analysis_id: response.analysis_id,
    product_id: response.product_id,
    product_name: response.product_name,
    brand: response.brand,
    main_goal: response.main_goal,
    raw_ingredient_list: response.raw_ingredient_list,
    skin_profile_snapshot: response.skin_profile_snapshot,
    parsed_formula_snapshot: response.parsed_formula_snapshot ?? [],
    compatibility_score: compatibilityScore,
    verdict: normalizeVerdict(response.verdict, compatibilityScore),
    irritation_risk: toPercent(response.irritation_risk),
    acne_risk: toPercent(response.acne_risk),
    benefit_score: toPercent(response.benefit_score),
    barrier_support: toPercent(response.barrier_support),
    applied_rules: appliedRules(response.applied_rules ?? []),
    positive_ingredients: ingredientReasons(response.positive_ingredients ?? [], "positive"),
    warning_ingredients: ingredientReasons(response.warning_ingredients ?? [], "warning"),
    unknown_ingredients: response.unknown_ingredients ?? [],
    recommendation: response.recommendation,
    disclaimer: response.disclaimer,
    created_at: response.created_at,
    feedback: response.feedback,
  };
}

export async function analyzeFormula(payload: AnalysisRequest): Promise<AnalysisResponse> {
  const backendPayload = {
    raw_ingredient_list: payload.raw_ingredient_list,
    ingredient_list: payload.raw_ingredient_list,
    skin_profile: payload.skin_profile,
    main_goal: payload.main_goal,
    product_name: payload.product_name,
    brand: payload.brand,
  };

  const response = await fetch(`${API_URL}/analysis`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(backendPayload),
  });

  if (!response.ok) {
    throw new Error("Analysis request failed");
  }

  return normalizeResponse((await response.json()) as BackendAnalysisResponse);
}

export async function getAnalysisHistory(): Promise<AnalysisHistoryItem[]> {
  const response = await fetch(`${API_URL}/analysis/history`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("History request failed");
  }

  const data = (await response.json()) as AnalysisHistoryItem[];
  return data.map((item) => ({
    ...item,
    verdict: normalizeVerdict(item.verdict, item.compatibility_score),
    compatibility_score: toPercent(item.compatibility_score),
    irritation_risk: toPercent(item.irritation_risk),
    acne_risk: toPercent(item.acne_risk),
    benefit_score: toPercent(item.benefit_score),
  }));
}

export async function getAnalysisDetail(analysisId: string): Promise<AnalysisDetail> {
  const response = await fetch(`${API_URL}/analysis/${analysisId}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Analysis detail request failed");
  }

  return normalizeDetail((await response.json()) as BackendAnalysisDetail);
}

export async function saveProductFeedback(
  analysisId: string,
  payload: ProductFeedbackRequest,
): Promise<ProductFeedbackResponse> {
  const response = await fetch(`${API_URL}/analysis/${analysisId}/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Feedback request failed");
  }

  return (await response.json()) as ProductFeedbackResponse;
}

export async function getPersonalInsights(): Promise<PersonalInsightsResponse> {
  const response = await fetch(`${API_URL}/insights/personal`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Personal insights request failed");
  }

  return (await response.json()) as PersonalInsightsResponse;
}

export async function extractFormulaFromImage(file: File): Promise<OcrFormulaResponse> {
  const formData = new FormData();
  formData.append("image", file);

  const response = await fetch(`${API_URL}/formulas/ocr`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "OCR request failed");
  }

  return (await response.json()) as OcrFormulaResponse;
}

export async function getSimilarProducts(productId: string): Promise<SimilarProduct[]> {
  const response = await fetch(`${API_URL}/products/${productId}/similar`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Similar products request failed");
  }

  const data = (await response.json()) as SimilarProduct[];
  return data.map((item) => ({
    ...item,
    similarity: toPercent(item.similarity),
  }));
}

export async function getRecommendations(payload: RecommendationRequest): Promise<RecommendationItem[]> {
  const response = await fetch(`${API_URL}/recommendations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Recommendations request failed");
  }

  return (await response.json()) as RecommendationItem[];
}

export async function generateRoutine(payload: {
  skin_profile: RecommendationRequest["skin_profile"];
  main_goal: RecommendationRequest["main_goal"];
  constraints: {
    avoid_ingredients: string[];
    max_steps: number;
  };
}): Promise<RoutineResponse> {
  const response = await fetch(`${API_URL}/routines/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Routine request failed");
  }

  return (await response.json()) as RoutineResponse;
}

export async function chatWithAgent(payload: AgentChatRequest): Promise<AgentChatResponse> {
  const response = await fetch(`${API_URL}/agent/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Agent request failed");
  }

  return (await response.json()) as AgentChatResponse;
}

export async function getCatalogProducts(filters: CatalogProductFilters = {}): Promise<CatalogProduct[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  });

  const query = params.toString();
  const response = await fetch(`${API_URL}/catalog/products${query ? `?${query}` : ""}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Catalog request failed");
  }

  return (await response.json()) as CatalogProduct[];
}
