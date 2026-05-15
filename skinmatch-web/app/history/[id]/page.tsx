"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FeedbackForm } from "@/components/FeedbackForm";
import { IngredientList } from "@/components/IngredientList";
import { RiskBadge } from "@/components/RiskBadge";
import { ScoreCard } from "@/components/ScoreCard";
import { getAnalysisDetail } from "@/lib/api";
import type { AnalysisDetail, ProductFeedbackResponse } from "@/types/analysis";

const verdictContent = {
  high_risk: { label: "Alto risco", tone: "high" as const },
  caution: { label: "Use com cautela", tone: "medium" as const },
  good_match: { label: "Boa compatibilidade", tone: "low" as const },
};

export default function AnalysisDetailPage() {
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalysisDetail(params.id)
      .then(setDetail)
      .catch(() => setError("Nao foi possivel carregar esta analise."))
      .finally(() => setLoading(false));
  }, [params.id]);

  function handleSaved(feedback: ProductFeedbackResponse) {
    setDetail((current) => (current ? { ...current, feedback } : current));
  }

  if (loading) {
    return <main className="min-h-screen px-4 py-8 text-sm text-moss sm:px-6 lg:px-8">Carregando analise...</main>;
  }

  if (error || !detail) {
    return <main className="min-h-screen px-4 py-8 text-sm text-rose-800 sm:px-6 lg:px-8">{error}</main>;
  }

  const verdict = verdictContent[detail.verdict];

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6">
        <header className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-ink">{detail.product_name || "Produto sem nome"}</h1>
              <p className="mt-2 text-sm text-moss">
                {detail.brand || "Marca nao informada"} · objetivo: {detail.main_goal}
              </p>
            </div>
            <RiskBadge label={verdict.label} tone={verdict.tone} />
          </div>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <ScoreCard title="Compatibilidade" value={detail.compatibility_score} interpretation="Score geral salvo nesta analise." />
          <ScoreCard title="Irritacao" value={detail.irritation_risk} interpretation="Risco estimado de irritacao." variant="risk" />
          <ScoreCard title="Acne" value={detail.acne_risk} interpretation="Risco estimado para tendencia acneica." variant="risk" />
          <ScoreCard title="Beneficio" value={detail.benefit_score} interpretation="Potencial positivo estimado." variant="benefit" />
        </div>

        <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Recomendacao</h2>
          <p className="mt-2 text-sm leading-6 text-moss">{detail.recommendation}</p>
        </section>

        <div className="grid gap-4 lg:grid-cols-3">
          <IngredientList title="Pontos positivos" items={detail.positive_ingredients} emptyText="Nenhum ponto positivo destacado." />
          <IngredientList title="Pontos de atencao" items={detail.warning_ingredients} emptyText="Nenhum ponto de atencao destacado." />
          <IngredientList title="Ingredientes nao reconhecidos" items={detail.unknown_ingredients} emptyText="Todos foram reconhecidos." />
        </div>

        <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Regras aplicadas</h2>
          <ul className="mt-4 grid gap-3">
            {detail.applied_rules.map((rule) => (
              <li key={rule.code} className="rounded-md bg-linen px-4 py-3 text-sm leading-6 text-moss">
                <strong className="mr-2 text-ink">{rule.code}</strong>
                {rule.label}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-ink">Formula original</h2>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-moss">{detail.raw_ingredient_list}</p>
        </section>

        {detail.feedback ? (
          <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
            <h2 className="text-lg font-semibold text-ink">Feedback registrado</h2>
            <p className="mt-2 text-sm leading-6 text-moss">
              Irritacao {detail.feedback.irritation_level}/5, acne {detail.feedback.acne_level}/5,
              ressecamento {detail.feedback.dryness_level}/5, satisfacao {detail.feedback.satisfaction_level}/5.
            </p>
            {detail.feedback.comments ? <p className="mt-3 text-sm leading-6 text-moss">{detail.feedback.comments}</p> : null}
          </section>
        ) : null}

        <FeedbackForm analysisId={detail.analysis_id} initialFeedback={detail.feedback} onSaved={handleSaved} />
      </div>
    </main>
  );
}
