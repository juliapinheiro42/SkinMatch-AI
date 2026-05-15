type ScoreCardProps = {
  title: string;
  value: number;
  interpretation: string;
  variant?: "score" | "risk" | "benefit";
};

function barColor(value: number, variant: ScoreCardProps["variant"]) {
  if (variant === "risk") {
    if (value >= 70) return "bg-rose-500";
    if (value >= 40) return "bg-amber-500";
    return "bg-emerald-500";
  }

  if (value >= 75) return "bg-emerald-600";
  if (value >= 50) return "bg-sage";
  return "bg-amber-500";
}

export function ScoreCard({ title, value, interpretation, variant = "score" }: ScoreCardProps) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-moss">{title}</h3>
        <strong className="text-2xl font-semibold text-ink">{value}</strong>
      </div>
      <div className="mt-4 h-2 w-full rounded-full bg-mist">
        <div
          className={`h-2 rounded-full ${barColor(value, variant)}`}
          style={{ width: `${value}%` }}
          aria-hidden="true"
        />
      </div>
      <p className="mt-3 text-sm leading-6 text-moss">{interpretation}</p>
    </section>
  );
}
