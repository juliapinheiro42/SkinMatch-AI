export type SkinType = "oily" | "dry" | "combination" | "normal";

export type MainGoal =
  | "acne"
  | "oil_control"
  | "barrier"
  | "hyperpigmentation"
  | "texture"
  | "anti_aging";

export type Verdict = "high_risk" | "caution" | "good_match";

export type SkinProfileInput = {
  skin_type: SkinType;
  sensitive_skin: boolean;
  acne_prone: boolean;
  barrier_compromised: boolean;
  known_triggers: string[];
  tolerated_ingredients: string[];
};

export type AnalysisRequest = {
  skin_profile: SkinProfileInput;
  main_goal: MainGoal;
  product_name?: string;
  brand?: string;
  raw_ingredient_list: string;
};

export type AppliedRule = {
  code: string;
  label: string;
};

export type IngredientReason = {
  name: string;
  reason: string;
};

export type AnalysisResponse = {
  analysis_id: string;
  product_id: string;
  compatibility_score: number;
  verdict: Verdict;
  irritation_risk: number;
  acne_risk: number;
  benefit_score: number;
  applied_rules: AppliedRule[];
  positive_ingredients: IngredientReason[];
  warning_ingredients: IngredientReason[];
  unknown_ingredients: string[];
  recommendation: string;
  disclaimer: string;
};

export type ParsedIngredient = {
  position: number;
  raw_name: string;
  normalized_name: string;
  inci_name: string;
  unknown: boolean;
  concentration_band: string;
};

export type AnalysisHistoryItem = {
  analysis_id: string;
  product_id?: string | null;
  product_name?: string | null;
  brand?: string | null;
  main_goal: MainGoal | string;
  compatibility_score: number;
  verdict: Verdict;
  irritation_risk: number;
  acne_risk: number;
  benefit_score: number;
  created_at: string;
};

export type ProductFeedbackRequest = {
  used_product: boolean;
  usage_days?: number | null;
  usage_frequency?: string | null;
  irritation_level: number;
  acne_level: number;
  dryness_level: number;
  satisfaction_level: number;
  noticed_benefits: string[];
  would_buy_again?: boolean | null;
  comments?: string | null;
};

export type ProductFeedbackResponse = ProductFeedbackRequest & {
  id: string;
  user_id: string;
  analysis_id: string;
  created_at: string;
};

export type AnalysisDetail = {
  analysis_id: string;
  product_id?: string | null;
  product_name?: string | null;
  brand?: string | null;
  main_goal: MainGoal | string;
  raw_ingredient_list: string;
  skin_profile_snapshot: SkinProfileInput;
  parsed_formula_snapshot: ParsedIngredient[];
  compatibility_score: number;
  verdict: Verdict;
  irritation_risk: number;
  acne_risk: number;
  benefit_score: number;
  barrier_support: number;
  applied_rules: AppliedRule[];
  positive_ingredients: IngredientReason[];
  warning_ingredients: IngredientReason[];
  unknown_ingredients: string[];
  recommendation: string;
  disclaimer: string;
  created_at: string;
  feedback?: ProductFeedbackResponse | null;
};

export type PersonalInsightsResponse = {
  total_feedbacks: number;
  common_triggers: Array<{
    ingredient: string;
    reaction: string;
    occurrences: number;
  }>;
  well_tolerated_ingredients: Array<{
    ingredient: string;
    positive_feedbacks: number;
  }>;
  patterns: string[];
  ingredient_affinity: {
    problematic: IngredientAffinityInsight[];
    well_tolerated: IngredientAffinityInsight[];
    low_confidence: IngredientAffinityInsight[];
  };
};

export type IngredientAffinityInsight = {
  ingredient_name: string;
  tolerance_score: number;
  confidence: number;
  feedback_count: number;
  confidence_label: "baixa" | "media" | "alta" | string;
};

export type OcrFormulaResponse = {
  extracted_text: string;
  cleaned_ingredient_list: string;
};

export type SimilarProduct = {
  product_id: string;
  name: string;
  brand: string;
  similarity: number;
};

export type RecommendationRequest = {
  skin_profile: SkinProfileInput;
  main_goal: MainGoal;
  exclude_ingredients: string[];
  constraints?: {
    price_range?: "low" | "mid" | "high" | null;
    preferred_category?: "cleanser" | "moisturizer" | "sunscreen" | "treatment" | null;
    routine_step_needed?: string | null;
    max_irritation_risk?: number | null;
    avoid_active_treatments?: boolean;
  };
  limit: number;
};

export type RecommendationItem = {
  product_id: string;
  name: string;
  brand: string;
  category?: string | null;
  compatibility_score: number;
  irritation_risk: number;
  acne_risk: number;
  benefit_score: number;
  final_score: number;
  score_breakdown: {
    compatibility: number;
    goal_match: number;
    safety: number;
    personalization: number;
    routine_fit?: number;
    price: number;
  };
  reason_codes: string[];
  reason: string;
  key_ingredients: string[];
};

export type RoutineStep = {
  step: number;
  type: "cleanser" | "toner" | "treatment" | "moisturizer" | "sunscreen" | string;
  product: {
    id: string;
    name: string;
    brand: string;
  };
  instructions: string;
  reason: string;
};

export type RoutineResponse = {
  morning_routine: RoutineStep[];
  night_routine: RoutineStep[];
  warnings: string[];
};

export type AgentChatContext = {
  product_name?: string;
  brand?: string;
  raw_ingredient_list?: string;
  skin_profile?: SkinProfileInput;
  main_goal?: MainGoal | string;
  exclude_ingredients?: string[];
};

export type AgentChatRequest = {
  user_id: string;
  message: string;
  context?: AgentChatContext;
};

export type AgentChatResponse = {
  answer: string;
  intent:
    | "analyze_product"
    | "recommend_products"
    | "generate_routine"
    | "explain_reaction"
    | "compare_products"
    | "adjust_routine"
    | "explain_ingredients"
    | "get_personal_insights"
    | "general_question"
    | "general_skincare_question"
    | "unknown";
  tools_used: string[];
  structured_result?: unknown;
  confidence?: "low" | "medium" | "high" | string;
  missing_info?: string[];
  follow_up_suggestion?: string | null;
  context_status?: string;
  risk_level?: "low" | "medium" | "high" | string;
  safety_disclaimer: string;
};

export type CatalogProduct = {
  product_id: string;
  name: string;
  brand: string;
  category?: string | null;
  routine_step?: string | null;
  usage_periods: string[];
  price_range?: string | null;
  tags: string[];
  is_active_treatment: boolean;
  is_sunscreen: boolean;
  is_moisturizer: boolean;
  is_cleanser: boolean;
  source?: string | null;
  source_url?: string | null;
  catalog_status: string;
};

export type CatalogProductFilters = {
  category?: string;
  routine_step?: string;
  tag?: string;
  price_range?: string;
  is_active_treatment?: boolean;
};
