import type { AgentChatContext } from "@/types/analysis";

type ProductContextBoxProps = {
  value: AgentChatContext;
  onChange: (value: AgentChatContext) => void;
};

export function ProductContextBox({ value, onChange }: ProductContextBoxProps) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
      <h2 className="text-base font-semibold text-ink">Contexto do produto</h2>
      <div className="mt-4 grid gap-4">
        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Produto</span>
          <input
            value={value.product_name ?? ""}
            onChange={(event) => onChange({ ...value, product_name: event.target.value })}
            className="rounded-md border border-ink/15 px-3 py-2 text-sm outline-none transition focus:border-sage"
            placeholder="Serum Antiacne X"
          />
        </label>
        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Marca</span>
          <input
            value={value.brand ?? ""}
            onChange={(event) => onChange({ ...value, brand: event.target.value })}
            className="rounded-md border border-ink/15 px-3 py-2 text-sm outline-none transition focus:border-sage"
            placeholder="Marca Y"
          />
        </label>
        <label className="grid gap-2">
          <span className="text-sm font-medium text-ink">Formula INCI</span>
          <textarea
            value={value.raw_ingredient_list ?? ""}
            onChange={(event) => onChange({ ...value, raw_ingredient_list: event.target.value })}
            className="min-h-32 rounded-md border border-ink/15 px-3 py-2 text-sm leading-6 outline-none transition focus:border-sage"
            placeholder="Aqua, Glycerin, Niacinamide..."
          />
        </label>
      </div>
    </section>
  );
}
