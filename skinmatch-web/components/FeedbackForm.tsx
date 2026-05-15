"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { type Resolver, useForm } from "react-hook-form";
import { saveProductFeedback } from "@/lib/api";
import { feedbackFormSchema, type FeedbackFormInput, type FeedbackFormValues } from "@/lib/schemas";
import type { ProductFeedbackResponse } from "@/types/analysis";

type FeedbackFormProps = {
  analysisId: string;
  initialFeedback?: ProductFeedbackResponse | null;
  onSaved?: (feedback: ProductFeedbackResponse) => void;
};

const benefits = [
  { value: "less_oiliness", label: "Menos oleosidade" },
  { value: "less_acne", label: "Menos acne" },
  { value: "smoother_texture", label: "Textura mais lisa" },
  { value: "less_redness", label: "Menos vermelhidao" },
  { value: "more_hydration", label: "Mais hidratacao" },
  { value: "brighter_skin", label: "Pele mais luminosa" },
];

function feedbackToDefaults(feedback?: ProductFeedbackResponse | null): Partial<FeedbackFormInput> {
  if (!feedback) {
    return {
      used_product: true,
      irritation_level: 0,
      acne_level: 0,
      dryness_level: 0,
      satisfaction_level: 3,
      noticed_benefits: [],
      would_buy_again: "unknown",
    };
  }

  return {
    used_product: feedback.used_product,
    usage_days: feedback.usage_days,
    usage_frequency: feedback.usage_frequency ?? "",
    irritation_level: feedback.irritation_level,
    acne_level: feedback.acne_level,
    dryness_level: feedback.dryness_level,
    satisfaction_level: feedback.satisfaction_level,
    noticed_benefits: feedback.noticed_benefits,
    would_buy_again:
      feedback.would_buy_again === null || feedback.would_buy_again === undefined
        ? "unknown"
        : feedback.would_buy_again
          ? "yes"
          : "no",
    comments: feedback.comments ?? "",
  };
}

export function FeedbackForm({ analysisId, initialFeedback, onSaved }: FeedbackFormProps) {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FeedbackFormInput, unknown, FeedbackFormValues>({
    resolver: zodResolver(feedbackFormSchema) as Resolver<FeedbackFormInput, unknown, FeedbackFormValues>,
    defaultValues: feedbackToDefaults(initialFeedback),
  });

  const usedProduct = watch("used_product");

  async function onSubmit(values: FeedbackFormValues) {
    setStatus(null);
    setError(null);

    try {
      const saved = await saveProductFeedback(analysisId, values);
      setStatus("Feedback salvo.");
      onSaved?.(saved);
    } catch {
      setError("Nao foi possivel salvar o feedback agora.");
    }
  }

  return (
    <form className="grid gap-5 rounded-lg border border-ink/10 bg-white p-6 shadow-soft" onSubmit={handleSubmit(onSubmit)}>
      <div>
        <h2 className="text-lg font-semibold text-ink">Feedback pos-uso</h2>
        <p className="mt-2 text-sm leading-6 text-moss">
          Registre como sua pele respondeu para melhorar os proximos sinais pessoais.
        </p>
      </div>

      <label className="flex min-h-12 items-center gap-3 rounded-md border border-ink/10 px-3 py-2">
        <input type="checkbox" className="h-4 w-4 accent-sage" {...register("used_product")} />
        <span className="text-sm text-ink">Usei este produto</span>
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Dias de uso</span>
          <input
            type="number"
            min={0}
            disabled={!usedProduct}
            className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20 disabled:bg-mist"
            {...register("usage_days")}
          />
          {errors.usage_days ? <span className="text-sm text-rose-700">{errors.usage_days.message}</span> : null}
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Frequencia</span>
          <select
            className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
            {...register("usage_frequency")}
          >
            <option value="">Selecione</option>
            <option value="daily">Diario</option>
            <option value="3x_per_week">3x por semana</option>
            <option value="weekly">Semanal</option>
            <option value="sporadic">Esporadico</option>
          </select>
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {[
          ["irritation_level", "Irritacao"],
          ["acne_level", "Acne"],
          ["dryness_level", "Ressecamento"],
          ["satisfaction_level", "Satisfacao"],
        ].map(([field, label]) => (
          <label key={field} className="grid gap-2">
            <span className="text-sm font-medium text-ink">{label}</span>
            <select
              className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
              {...register(field as keyof FeedbackFormInput)}
            >
              {[0, 1, 2, 3, 4, 5].map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      <fieldset className="grid gap-3">
        <legend className="text-sm font-medium text-ink">Beneficios percebidos</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {benefits.map((benefit) => (
            <label key={benefit.value} className="flex min-h-11 items-center gap-3 rounded-md border border-ink/10 px-3 py-2">
              <input
                type="checkbox"
                value={benefit.value}
                className="h-4 w-4 accent-sage"
                {...register("noticed_benefits")}
              />
              <span className="text-sm text-ink">{benefit.label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <label className="grid gap-2">
        <span className="text-sm font-medium text-ink">Compraria novamente?</span>
        <select
          className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
          {...register("would_buy_again")}
        >
          <option value="unknown">Nao sei</option>
          <option value="yes">Sim</option>
          <option value="no">Nao</option>
        </select>
      </label>

      <label className="grid gap-2">
        <span className="text-sm font-medium text-ink">Comentarios</span>
        <textarea
          className="min-h-28 rounded-md border border-ink/15 bg-white px-3 py-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
          placeholder="Funcionou, mas ardeu um pouco nos primeiros dias."
          {...register("comments")}
        />
      </label>

      {status ? <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{status}</p> : null}
      {error ? <p className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <button
        type="submit"
        disabled={isSubmitting}
        className="h-12 rounded-md bg-ink px-5 text-sm font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Salvando..." : "Salvar feedback"}
      </button>
    </form>
  );
}
