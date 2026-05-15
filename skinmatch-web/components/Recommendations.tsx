"use client";

import { useState } from "react";
import { generateRoutine, getRecommendations } from "@/lib/api";
import { RoutineView } from "@/components/RoutineView";
import type { AnalysisRequest, RecommendationItem, RoutineResponse } from "@/types/analysis";

type RecommendationsProps = {
  analysisPayload: AnalysisRequest;
};

export function Recommendations({ analysisPayload }: RecommendationsProps) {
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routineError, setRoutineError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [routine, setRoutine] = useState<RoutineResponse | null>(null);
  const [routineLoading, setRoutineLoading] = useState(false);
  const [openBreakdown, setOpenBreakdown] = useState<string | null>(null);

  async function loadRecommendations() {
    setLoading(true);
    setError(null);

    try {
      const recommendations = await getRecommendations({
        skin_profile: analysisPayload.skin_profile,
        main_goal: analysisPayload.main_goal,
        exclude_ingredients: analysisPayload.skin_profile.known_triggers,
        constraints: {
          max_irritation_risk: analysisPayload.skin_profile.sensitive_skin ? 70 : undefined,
        },
        limit: 5,
      });
      setItems(recommendations);
      setLoaded(true);
    } catch {
      setError("Nao foi possivel buscar alternativas agora.");
    } finally {
      setLoading(false);
    }
  }

  async function loadRoutine() {
    setRoutineLoading(true);
    setRoutineError(null);

    try {
      const generated = await generateRoutine({
        skin_profile: analysisPayload.skin_profile,
        main_goal: analysisPayload.main_goal,
        constraints: {
          avoid_ingredients: analysisPayload.skin_profile.known_triggers,
          max_steps: 5,
        },
      });
      setRoutine(generated);
    } catch {
      setRoutineError("Nao foi possivel gerar a rotina agora.");
    } finally {
      setRoutineLoading(false);
    }
  }

  function badgesFor(item: RecommendationItem): string[] {
    const ingredients = item.key_ingredients.map((ingredient) => ingredient.toLowerCase());
    const badges = [];
    if (item.reason_codes.includes("avoids_explicit_trigger") || item.reason_codes.includes("avoids_known_triggers")) {
      badges.push("Sem fragrância");
    }
    if (item.reason_codes.includes("low_irritation_risk")) {
      badges.push("Baixo risco");
    }
    if (ingredients.includes("niacinamide")) {
      badges.push("Contém niacinamide");
    }
    if (item.reason_codes.includes("matches_price_preference") || item.reason_codes.includes("matches_price_range")) {
      badges.push("Barato");
    }
    if (item.reason_codes.some((code) => code.includes("acne"))) {
      badges.push("Combina com acne");
    }
    return badges;
  }

  return (
    <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-ink">Produtos mais compativeis com voce</h2>
          <p className="mt-2 text-sm leading-6 text-moss">
            Sugestoes geradas apenas a partir dos produtos ja analisados na base.
          </p>
        </div>
        <button
          type="button"
          onClick={loadRecommendations}
          disabled={loading}
          className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Buscando..." : "Ver alternativas melhores"}
        </button>
        <button
          type="button"
          onClick={loadRoutine}
          disabled={routineLoading}
          className="rounded-md border border-ink/15 px-4 py-2 text-sm font-semibold text-ink transition hover:bg-linen disabled:cursor-not-allowed disabled:opacity-60"
        >
          {routineLoading ? "Gerando..." : "Gerar rotina completa"}
        </button>
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}
      {routineError ? <p className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-800">{routineError}</p> : null}

      {loaded && items.length === 0 ? (
        <p className="mt-5 rounded-md bg-linen px-4 py-3 text-sm text-moss">
          Ainda nao ha produtos seguros o suficiente para recomendar com esses filtros.
        </p>
      ) : null}

      {items.length > 0 ? (
        <div className="mt-5 grid gap-4">
          {items.map((item) => (
            <article key={item.product_id} className="rounded-md border border-ink/10 bg-linen p-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-ink">{item.name}</h3>
                  <p className="mt-1 text-sm text-moss">{item.brand}</p>
                  {item.category ? <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-moss">{item.category}</p> : null}
                </div>
                <div className="text-right">
                  <span className="text-xs font-semibold uppercase tracking-wide text-moss">score final</span>
                  <strong className="block text-2xl font-semibold text-ink">{item.final_score ?? item.compatibility_score}%</strong>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-moss">{item.reason}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {badgesFor(item).map((badge) => (
                  <span key={badge} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-ink">
                    {badge}
                  </span>
                ))}
              </div>
              {item.key_ingredients.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.key_ingredients.map((ingredient) => (
                    <span key={ingredient} className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-moss">
                      {ingredient}
                    </span>
                  ))}
                </div>
              ) : null}
              <button
                type="button"
                onClick={() => setOpenBreakdown(openBreakdown === item.product_id ? null : item.product_id)}
                className="mt-4 rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink transition hover:bg-white"
              >
                Ver por que foi recomendado
              </button>
              {openBreakdown === item.product_id ? (
                <div className="mt-4 grid gap-2 rounded-md bg-white p-4 text-sm text-moss sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    ["Compatibilidade", item.score_breakdown?.compatibility],
                    ["Seguranca", item.score_breakdown?.safety],
                    ["Objetivo", item.score_breakdown?.goal_match],
                    ["Personalizacao", item.score_breakdown?.personalization],
                    ["Preco", item.score_breakdown?.price],
                  ].map(([label, value]) => (
                    <div key={label} className="rounded-md border border-ink/10 px-3 py-2">
                      <span className="block text-xs uppercase tracking-wide">{label}</span>
                      <strong className="text-lg text-ink">{Number(value ?? 0)}%</strong>
                    </div>
                  ))}
                  {item.reason_codes.length > 0 ? (
                    <div className="sm:col-span-2 lg:col-span-3">
                      <span className="text-xs uppercase tracking-wide">Sinais usados</span>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {item.reason_codes.map((code) => (
                          <span key={code} className="rounded-full bg-linen px-3 py-1 text-xs font-semibold text-moss">
                            {code}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <button
                type="button"
                className="mt-3 rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink transition hover:bg-white"
              >
                Analisar este produto
              </button>
            </article>
          ))}
        </div>
      ) : null}

      {routine ? (
        <div className="mt-6">
          <RoutineView routine={routine} />
        </div>
      ) : null}
    </section>
  );
}
