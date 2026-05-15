"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAnalysisHistory } from "@/lib/api";
import type { AnalysisHistoryItem } from "@/types/analysis";
import { RiskBadge } from "@/components/RiskBadge";

const verdictContent = {
  high_risk: { label: "Alto risco", tone: "high" as const },
  caution: { label: "Cautela", tone: "medium" as const },
  good_match: { label: "Bom match", tone: "low" as const },
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function HistoryPage() {
  const [items, setItems] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalysisHistory()
      .then(setItems)
      .catch(() => setError("Nao foi possivel carregar o historico."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6">
        <header className="grid gap-2">
          <h1 className="text-3xl font-semibold text-ink">Historico</h1>
          <p className="text-sm leading-6 text-moss">Analises salvas automaticamente para o usuario temporario do MVP.</p>
        </header>

        {loading ? (
          <section className="rounded-lg border border-ink/10 bg-white p-6 text-sm text-moss shadow-soft">Carregando historico...</section>
        ) : null}

        {error ? (
          <section className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">{error}</section>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <section className="rounded-lg border border-dashed border-ink/20 bg-white/70 p-8 text-center shadow-soft">
            <h2 className="text-lg font-semibold text-ink">Nenhuma analise salva</h2>
            <p className="mt-2 text-sm text-moss">Quando voce fizer uma nova analise, ela aparecera aqui.</p>
          </section>
        ) : null}

        <div className="grid gap-4">
          {items.map((item) => {
            const verdict = verdictContent[item.verdict];
            const title = item.product_name || "Produto sem nome";

            return (
              <article key={item.analysis_id} className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="grid gap-1">
                    <h2 className="text-lg font-semibold text-ink">{title}</h2>
                    <p className="text-sm text-moss">
                      {item.brand || "Marca nao informada"} · {item.main_goal} · {formatDate(item.created_at)}
                    </p>
                  </div>
                  <RiskBadge label={verdict.label} tone={verdict.tone} />
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-4">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-moss">Score</span>
                    <p className="mt-1 text-2xl font-semibold text-ink">{item.compatibility_score}</p>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-moss">Irritacao</span>
                    <p className="mt-1 text-lg font-semibold text-ink">{item.irritation_risk}</p>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-moss">Acne</span>
                    <p className="mt-1 text-lg font-semibold text-ink">{item.acne_risk}</p>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-moss">Beneficio</span>
                    <p className="mt-1 text-lg font-semibold text-ink">{item.benefit_score}</p>
                  </div>
                </div>

                <Link
                  href={`/history/${item.analysis_id}`}
                  className="mt-5 inline-flex rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-moss"
                >
                  Ver detalhes
                </Link>
              </article>
            );
          })}
        </div>
      </div>
    </main>
  );
}
