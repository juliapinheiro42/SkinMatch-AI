import type { FieldErrors, UseFormRegister } from "react-hook-form";
import type { AnalysisFormInput } from "@/lib/schemas";

type SkinProfileFormProps = {
  register: UseFormRegister<AnalysisFormInput>;
  errors: FieldErrors<AnalysisFormInput>;
};

const skinTypes = [
  { value: "oily", label: "Oleosa" },
  { value: "dry", label: "Seca" },
  { value: "combination", label: "Mista" },
  { value: "normal", label: "Normal" },
] as const;

export function SkinProfileForm({ register, errors }: SkinProfileFormProps) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">Perfil de pele</h2>

      <div className="mt-5 grid gap-5">
        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Tipo de pele</span>
          <select
            className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
            {...register("skin_type")}
          >
            <option value="">Selecione</option>
            {skinTypes.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          {errors.skin_type ? <span className="text-sm text-rose-700">{errors.skin_type.message}</span> : null}
        </label>

        <div className="grid gap-3 sm:grid-cols-3">
          <label className="flex min-h-12 items-center gap-3 rounded-md border border-ink/10 px-3 py-2">
            <input type="checkbox" className="h-4 w-4 accent-sage" {...register("sensitive_skin")} />
            <span className="text-sm text-ink">Pele sensivel</span>
          </label>
          <label className="flex min-h-12 items-center gap-3 rounded-md border border-ink/10 px-3 py-2">
            <input type="checkbox" className="h-4 w-4 accent-sage" {...register("acne_prone")} />
            <span className="text-sm text-ink">Tendencia a acne</span>
          </label>
          <label className="flex min-h-12 items-center gap-3 rounded-md border border-ink/10 px-3 py-2">
            <input type="checkbox" className="h-4 w-4 accent-sage" {...register("barrier_compromised")} />
            <span className="text-sm text-ink">Barreira sensibilizada</span>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Gatilhos conhecidos</span>
            <input
              className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
              placeholder="fragrance, alcohol denat"
              {...register("known_triggers")}
            />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Ingredientes tolerados</span>
            <input
              className="h-11 rounded-md border border-ink/15 bg-white px-3 text-ink outline-none transition focus:border-sage focus:ring-2 focus:ring-sage/20"
              placeholder="niacinamide, glycerin"
              {...register("tolerated_ingredients")}
            />
          </label>
        </div>
      </div>
    </section>
  );
}
