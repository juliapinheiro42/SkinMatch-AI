import type { FieldErrors, UseFormRegister } from "react-hook-form";
import type { AnalysisFormInput } from "@/lib/schemas";

type FormulaFormProps = {
  register: UseFormRegister<AnalysisFormInput>;
  errors: FieldErrors<AnalysisFormInput>;
};

const goals = [
  { value: "acne", label: "Acne" },
  { value: "oil_control", label: "Controle de oleosidade" },
  { value: "barrier", label: "Barreira cutanea" },
  { value: "hyperpigmentation", label: "Manchas" },
  { value: "texture", label: "Textura" },
  { value: "anti_aging", label: "Anti-aging" },
] as const;

export function FormulaForm({ register, errors }: FormulaFormProps) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">Produto e formula</h2>

      <div className="mt-5 grid gap-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Nome do produto</span>
            <input
              className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
              placeholder="Serum Antiacne X"
              {...register("product_name")}
            />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Marca</span>
            <input
              className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
              placeholder="Marca Y"
              {...register("brand")}
            />
          </label>
        </div>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Objetivo principal</span>
          <select
            className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
            {...register("main_goal")}
          >
            <option value="">Selecione</option>
            {goals.map((goal) => (
              <option key={goal.value} value={goal.value}>
                {goal.label}
              </option>
            ))}
          </select>
          {errors.main_goal ? <span className="text-sm text-rose-700">{errors.main_goal.message}</span> : null}
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Lista INCI</span>
          <textarea
            className="min-h-40 rounded-md border border-ink/15 bg-white px-3 py-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
            placeholder="Aqua, Glycerin, Niacinamide, Salicylic Acid, Alcohol Denat., Parfum"
            {...register("raw_ingredient_list")}
          />
          {errors.raw_ingredient_list ? (
            <span className="text-sm text-rose-700">{errors.raw_ingredient_list.message}</span>
          ) : null}
        </label>
      </div>
    </section>
  );
}
