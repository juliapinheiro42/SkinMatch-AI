import Link from "next/link";
import type { AnalysisResponse } from "@/types/analysis";
import { Disclaimer } from "@/components/Disclaimer";
import { IngredientList } from "@/components/IngredientList";
import { RiskBadge } from "@/components/RiskBadge";
import { ScoreCard } from "@/components/ScoreCard";

type AnalysisResultProps = {
  result: AnalysisResponse;
};

const verdictContent = {
  high_risk: {
    label: "Alto risco",
    description: "Essa formula pode nao ser uma boa escolha para o seu perfil.",
    tone: "high" as const,
  },
  caution: {
    label: "Use com cautela",
    description: "A formula tem pontos positivos, mas tambem riscos relevantes.",
    tone: "medium" as const,
  },
  good_match: {
    label: "Boa compatibilidade",
    description: "A formula parece compativel com seu perfil, considerando os dados informados.",
    tone: "low" as const,
  },
};

function riskInterpretation(value: number) {
  if (value >= 70) return "Estimativa elevada com base no perfil informado.";
  if (value >= 40) return "Estimativa moderada; vale observar tolerancia individual.";
  return "Estimativa baixa dentro dos dados avaliados.";
}

export function AnalysisResult({ result }: AnalysisResultProps) {
  const verdict = verdictContent[result.verdict];

  return (
    <section className="grid gap-6">
      <div className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold text-ink">Resultado da analise</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-moss">{verdict.description}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <RiskBadge label={verdict.label} tone={verdict.tone} />
            <Link
              href={`/history/${result.analysis_id}`}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink transition hover:bg-linen"
            >
              Ver detalhes
            </Link>
            <Link
              href={`/products/${result.product_id}/similar`}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm font-semibold text-ink transition hover:bg-linen"
            >
              Ver produtos similares
            </Link>
          </div>
        </div>
        <p className="mt-4 text-xs text-moss">Produto identificado: {result.product_id}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ScoreCard
          title="Compatibilidade"
          value={result.compatibility_score}
          interpretation="Estimativa geral de match com base no perfil informado."
        />
        <ScoreCard
          title="Risco de irritacao"
          value={result.irritation_risk}
          interpretation={riskInterpretation(result.irritation_risk)}
          variant="risk"
        />
        <ScoreCard
          title="Risco de acne"
          value={result.acne_risk}
          interpretation={riskInterpretation(result.acne_risk)}
          variant="risk"
        />
        <ScoreCard
          title="Beneficio esperado"
          value={result.benefit_score}
          interpretation="Potencial positivo estimado para os objetivos e caracteristicas informadas."
          variant="benefit"
        />
      </div>

      <div className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
        <h3 className="text-base font-semibold text-ink">Recomendacao</h3>
        <p className="mt-2 text-sm leading-6 text-moss">{result.recommendation}</p>
      </div>

      {result.applied_rules.length > 0 ? (
        <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
          <h3 className="text-base font-semibold text-ink">Sinais considerados</h3>
          <ul className="mt-4 grid gap-3">
            {result.applied_rules.map((rule) => (
              <li key={rule.code} className="rounded-md bg-linen px-4 py-3 text-sm leading-6 text-moss">
                <strong className="mr-2 text-ink">{rule.code}</strong>
                {rule.label}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <IngredientList
          title="Pontos positivos"
          items={result.positive_ingredients}
          emptyText="Nenhum ponto positivo especifico foi destacado nesta estimativa."
        />
        <IngredientList
          title="Pontos de atencao"
          items={result.warning_ingredients}
          emptyText="Nenhum ponto de atencao especifico foi destacado nesta estimativa."
        />
        <IngredientList
          title="Ingredientes nao reconhecidos"
          items={result.unknown_ingredients}
          emptyText="Todos os ingredientes avaliados foram reconhecidos pelo motor atual."
        />
      </div>

      <Disclaimer text={result.disclaimer} />
    </section>
  );
}
