type RoutineProduct = {
  id?: string;
  name?: string;
  brand?: string;
} | null;

type RoutineStepResult = {
  step?: number;
  type?: string;
  product?: RoutineProduct;
  instructions?: string;
  reason?: string;
};

type RoutineStructuredResult = {
  morning_routine?: RoutineStepResult[];
  night_routine?: RoutineStepResult[];
  warnings?: string[];
};

type RoutineResultCardProps = {
  routine: RoutineStructuredResult;
};

const labels: Record<string, string> = {
  cleanser: "Limpeza",
  toner: "Tonico",
  treatment: "Tratamento",
  moisturizer: "Hidratante",
  sunscreen: "Protetor solar",
};

function RoutineSection({
  title,
  emptyText,
  steps,
}: {
  title: string;
  emptyText: string;
  steps: RoutineStepResult[];
}) {
  return (
    <section className="rounded-md bg-white p-4">
      <h4 className="text-sm font-semibold text-ink">{title}</h4>
      <div className="mt-3 grid gap-3">
        {steps.length === 0 ? <p className="text-sm leading-6 text-moss">{emptyText}</p> : null}
        {steps.map((step, index) => {
          const type = step.type ?? "etapa";
          const productName = [step.product?.brand, step.product?.name].filter(Boolean).join(" ");
          return (
            <article key={`${type}-${index}`} className="rounded-md border border-ink/10 bg-linen p-3">
              <div className="flex gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-ink text-xs font-semibold text-white">
                  {step.step ?? index + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide text-moss">{labels[type] ?? type}</p>
                  {productName ? <p className="mt-1 text-sm font-semibold text-ink">{productName}</p> : null}
                  {step.instructions ? (
                    <p className="mt-2 text-sm leading-6 text-ink">Como usar: {step.instructions}</p>
                  ) : null}
                  {step.reason ? <p className="mt-1 text-sm leading-6 text-moss">Por quê: {step.reason}</p> : null}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function isRoutineResult(value: unknown): value is RoutineStructuredResult {
  return (
    typeof value === "object" &&
    value !== null &&
    ("morning_routine" in value || "night_routine" in value)
  );
}

export function RoutineResultCard({ routine }: RoutineResultCardProps) {
  const morning = routine.morning_routine ?? [];
  const night = routine.night_routine ?? [];
  const warnings = routine.warnings ?? [];

  return (
    <section className="grid gap-4 rounded-lg border border-ink/10 bg-linen p-4">
      <div>
        <span className="text-xs font-semibold uppercase tracking-wide text-sage">Rotina gerada</span>
        <p className="mt-1 text-sm leading-6 text-moss">
          Comece devagar e introduza um produto novo por vez.
        </p>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <RoutineSection title="Manha" emptyText="Nenhuma etapa encontrada para manha." steps={morning} />
        <RoutineSection title="Noite" emptyText="Nenhuma etapa encontrada para noite." steps={night} />
      </div>

      <section className="rounded-md border border-amber-200 bg-amber-50 p-4">
        <h4 className="text-sm font-semibold text-amber-900">Cuidados</h4>
        {warnings.length ? (
          <ul className="mt-2 grid gap-1">
            {warnings.map((warning) => (
              <li key={warning} className="text-sm leading-6 text-amber-900">
                {warning}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm leading-6 text-amber-900">Introduza novos produtos gradualmente.</p>
        )}
      </section>
    </section>
  );
}
