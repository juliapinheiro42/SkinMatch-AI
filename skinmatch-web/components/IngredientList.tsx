import type { IngredientReason } from "@/types/analysis";

type IngredientListProps = {
  title: string;
  items: IngredientReason[] | string[];
  emptyText: string;
};

function isReasonItem(item: IngredientReason | string): item is IngredientReason {
  return typeof item === "object" && "name" in item;
}

export function IngredientList({ title, items, emptyText }: IngredientListProps) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-3 text-sm leading-6 text-moss">{emptyText}</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((item) => {
            const name = isReasonItem(item) ? item.name : item;
            const reason = isReasonItem(item) ? item.reason : undefined;

            return (
              <li key={name} className="rounded-md bg-linen px-4 py-3">
                <span className="block text-sm font-semibold capitalize text-ink">{name}</span>
                {reason ? <span className="mt-1 block text-sm leading-6 text-moss">{reason}</span> : null}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
