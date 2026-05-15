type ToolResultCardProps = {
  toolsUsed: string[];
  structuredResult?: unknown;
};

function isAnalysisResult(value: unknown): value is {
  compatibility_score: number;
  verdict: string;
  irritation_risk?: number;
  acne_risk?: number;
  benefit_score?: number;
} {
  return typeof value === "object" && value !== null && "compatibility_score" in value && "verdict" in value;
}

export function ToolResultCard({ toolsUsed, structuredResult }: ToolResultCardProps) {
  if (!toolsUsed.length && !structuredResult) {
    return null;
  }

  return (
    <section className="rounded-lg border border-ink/10 bg-linen p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-sage">Ferramentas usadas</span>
        {toolsUsed.length ? (
          toolsUsed.map((tool) => (
            <span key={tool} className="rounded-md bg-white px-2 py-1 text-xs font-medium text-moss">
              {tool}
            </span>
          ))
        ) : (
          <span className="text-xs text-moss">Nenhuma ferramenta chamada</span>
        )}
      </div>

      {isAnalysisResult(structuredResult) ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <div>
            <p className="text-xs text-moss">Score</p>
            <p className="text-lg font-semibold text-ink">{structuredResult.compatibility_score}%</p>
          </div>
          <div>
            <p className="text-xs text-moss">Veredito</p>
            <p className="text-sm font-semibold text-ink">{structuredResult.verdict}</p>
          </div>
          <div>
            <p className="text-xs text-moss">Irritacao</p>
            <p className="text-sm font-semibold text-ink">{structuredResult.irritation_risk ?? "-"} </p>
          </div>
          <div>
            <p className="text-xs text-moss">Acne</p>
            <p className="text-sm font-semibold text-ink">{structuredResult.acne_risk ?? "-"} </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
