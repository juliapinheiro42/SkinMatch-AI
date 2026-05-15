"use client";

import { useEffect, useState } from "react";
import { getPersonalInsights } from "@/lib/api";
import type { IngredientAffinityInsight, PersonalInsightsResponse } from "@/types/analysis";

function AffinityList({ items, empty }: { items: IngredientAffinityInsight[]; empty: string }) {
  if (items.length === 0) {
    return <li className="text-sm text-moss">{empty}</li>;
  }
  return (
    <>
      {items.map((item) => (
        <li key={item.ingredient_name} className="rounded-md bg-linen px-4 py-3 text-sm text-ink">
          <span className="font-semibold">{item.ingredient_name}</span>
          <span className="mt-1 block text-moss">
            tolerancia {item.tolerance_score.toFixed(2)} · confianca {item.confidence_label} · {item.feedback_count} feedback(s)
          </span>
        </li>
      ))}
    </>
  );
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<PersonalInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPersonalInsights()
      .then(setInsights)
      .catch(() => setError("Nao foi possivel carregar seus insights."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6">
        <header className="grid gap-2">
          <h1 className="text-3xl font-semibold text-ink">Insights pessoais</h1>
          <p className="text-sm leading-6 text-moss">
            Estes insights sao baseados nos feedbacks que voce registrou e nao representam diagnostico medico.
          </p>
        </header>

        {loading ? <section className="rounded-lg border border-ink/10 bg-white p-6 text-sm text-moss shadow-soft">Carregando insights...</section> : null}
        {error ? <section className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">{error}</section> : null}

        {insights ? (
          <div className="grid gap-6">
            <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
              <span className="text-sm font-semibold uppercase tracking-wide text-moss">Feedbacks registrados</span>
              <p className="mt-2 text-4xl font-semibold text-ink">{insights.total_feedbacks}</p>
            </section>

            <div className="grid gap-6 lg:grid-cols-2">
              <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
                <h2 className="text-lg font-semibold text-ink">Possiveis gatilhos</h2>
                <ul className="mt-4 grid gap-3">
                  {insights.common_triggers.length === 0 ? <li className="text-sm text-moss">Nenhum gatilho detectado ainda.</li> : null}
                  {insights.common_triggers.map((item) => (
                    <li key={item.ingredient} className="rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-900">
                      {item.ingredient} · {item.occurrences} ocorrencia(s)
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
                <h2 className="text-lg font-semibold text-ink">Ingredientes bem tolerados</h2>
                <ul className="mt-4 grid gap-3">
                  {insights.well_tolerated_ingredients.length === 0 ? <li className="text-sm text-moss">Nenhum ingrediente destacado ainda.</li> : null}
                  {insights.well_tolerated_ingredients.map((item) => (
                    <li key={item.ingredient} className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                      {item.ingredient} · {item.positive_feedbacks} feedback(s) positivo(s)
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
              <div className="grid gap-1">
                <h2 className="text-lg font-semibold text-ink">Como sua pele parece reagir</h2>
                <p className="text-sm leading-6 text-moss">
                  Estes padroes sao estimativas baseadas nos feedbacks que voce registrou.
                </p>
              </div>
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-rose-800">Possivelmente problematicos</h3>
                  <ul className="mt-3 grid gap-3">
                    <AffinityList
                      items={insights.ingredient_affinity?.problematic ?? []}
                      empty="Ainda nao ha ingredientes com tolerancia negativa suficiente."
                    />
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">Bem tolerados</h3>
                  <ul className="mt-3 grid gap-3">
                    <AffinityList
                      items={insights.ingredient_affinity?.well_tolerated ?? []}
                      empty="Ainda nao ha ingredientes com tolerancia positiva suficiente."
                    />
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-moss">Baixa confianca</h3>
                  <ul className="mt-3 grid gap-3">
                    <AffinityList
                      items={insights.ingredient_affinity?.low_confidence ?? []}
                      empty="Sem sinais de baixa confianca no momento."
                    />
                  </ul>
                </div>
              </div>
            </section>

            <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
              <h2 className="text-lg font-semibold text-ink">Padroes detectados</h2>
              <ul className="mt-4 grid gap-3">
                {insights.patterns.length === 0 ? <li className="text-sm text-moss">Registre mais feedbacks para ver padroes.</li> : null}
                {insights.patterns.map((pattern) => (
                  <li key={pattern} className="rounded-md bg-linen px-4 py-3 text-sm leading-6 text-moss">
                    {pattern}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        ) : null}
      </div>
    </main>
  );
}
