import { z } from "zod";

const commaSeparatedArray = z
  .string()
  .optional()
  .transform((value) =>
    (value ?? "")
      .split(",")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean),
  );

export const analysisFormSchema = z.object({
  skin_type: z.enum(["oily", "dry", "combination", "normal"], {
    required_error: "Selecione seu tipo de pele.",
  }),
  sensitive_skin: z.boolean().default(false),
  acne_prone: z.boolean().default(false),
  barrier_compromised: z.boolean().default(false),
  known_triggers: commaSeparatedArray,
  tolerated_ingredients: commaSeparatedArray,
  product_name: z.string().trim().optional(),
  brand: z.string().trim().optional(),
  main_goal: z.enum(["acne", "oil_control", "barrier", "hyperpigmentation", "texture", "anti_aging"], {
    required_error: "Selecione o objetivo principal.",
  }),
  raw_ingredient_list: z
    .string()
    .trim()
    .min(1, "Cole a lista INCI do produto.")
    .refine(
      (value) => value.split(",").map((item) => item.trim()).filter(Boolean).length >= 3,
      "Informe pelo menos 3 ingredientes separados por virgula.",
    ),
});

export type AnalysisFormInput = z.input<typeof analysisFormSchema>;
export type AnalysisFormValues = z.output<typeof analysisFormSchema>;

export const feedbackFormSchema = z
  .object({
    used_product: z.boolean().default(true),
    usage_days: z.coerce.number().int().min(0).optional().nullable(),
    usage_frequency: z.string().trim().optional().nullable(),
    irritation_level: z.coerce.number().int().min(0).max(5),
    acne_level: z.coerce.number().int().min(0).max(5),
    dryness_level: z.coerce.number().int().min(0).max(5),
    satisfaction_level: z.coerce.number().int().min(0).max(5),
    noticed_benefits: z.array(z.string()).default([]),
    would_buy_again: z
      .enum(["yes", "no", "unknown"])
      .default("unknown")
      .transform((value) => (value === "unknown" ? null : value === "yes")),
    comments: z.string().trim().optional().nullable(),
  })
  .refine((value) => !value.used_product || value.usage_days != null, {
    path: ["usage_days"],
    message: "Informe por quantos dias voce usou o produto.",
  });

export type FeedbackFormInput = z.input<typeof feedbackFormSchema>;
export type FeedbackFormValues = z.output<typeof feedbackFormSchema>;
