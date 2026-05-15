import type { RoutineResponse, RoutineStep } from "@/types/analysis";

type RoutineViewProps = {
  routine: RoutineResponse;
};

const labels: Record<string, string> = {
  cleanser: "Limpeza",
  toner: "Tonico",
  treatment: "Tratamento",
  moisturizer: "Hidratante",
  sunscreen: "Protetor solar",
};

function RoutineColumn({ title, steps }: { title: string; steps: RoutineStep[] }) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
      <h3 className="text-lg font-semibold text-ink">{title}</h3>
      <div className="mt-4 grid gap-3">
        {steps.length === 0 ? <p className="text-sm text-moss">Nenhum passo selecionado com os filtros atuais.</p> : null}
        {steps.map((step) => (
          <article key={`${step.type}-${step.product.id}`} className="rounded-md bg-linen p-4">
            <div className="flex items-start gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-sm font-semibold text-white">
                {step.step}
              </span>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-moss">{labels[step.type] ?? step.type}</p>
                <h4 className="mt-1 text-base font-semibold text-ink">{step.product.name}</h4>
                <p className="mt-1 text-sm text-moss">{step.product.brand}</p>
                <p className="mt-3 text-sm leading-6 text-ink">{step.instructions}</p>
                <p className="mt-2 text-sm leading-6 text-moss">{step.reason}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function RoutineView({ routine }: RoutineViewProps) {
  return (
    <section className="grid gap-5">
      <div className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
        <h2 className="text-xl font-semibold text-ink">Rotina completa</h2>
        <p className="mt-2 text-sm leading-6 text-moss">
          Comece devagar, observe sua pele e ajuste a frequencia conforme tolerancia.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <RoutineColumn title="Manha" steps={routine.morning_routine} />
        <RoutineColumn title="Noite" steps={routine.night_routine} />
      </div>

      {routine.warnings.length > 0 ? (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <h3 className="text-base font-semibold text-amber-900">Cuidados importantes</h3>
          <ul className="mt-3 grid gap-2">
            {routine.warnings.map((warning) => (
              <li key={warning} className="text-sm leading-6 text-amber-900">
                {warning}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </section>
  );
}
