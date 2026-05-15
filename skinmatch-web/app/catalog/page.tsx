"use client";

import { useEffect, useState } from "react";
import { getCatalogProducts } from "@/lib/api";
import type { CatalogProduct, CatalogProductFilters } from "@/types/analysis";

const categories = ["", "cleanser", "moisturizer", "sunscreen", "acne_treatment", "barrier_repair"];
const steps = ["", "cleanser", "treatment", "moisturizer", "sunscreen"];
const prices = ["", "low", "mid", "high"];

export default function CatalogPage() {
  const [filters, setFilters] = useState<CatalogProductFilters>({});
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    getCatalogProducts(filters)
      .then((items) => {
        if (active) {
          setProducts(items);
        }
      })
      .catch(() => {
        if (active) {
          setError("Nao foi possivel carregar o catalogo. Verifique se o backend esta rodando.");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [filters]);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6">
        <header className="grid gap-2">
          <p className="text-sm font-semibold uppercase tracking-wide text-sage">Catalogo</p>
          <h1 className="text-3xl font-semibold text-ink">Produtos cadastrados</h1>
          <p className="max-w-2xl text-sm leading-6 text-moss">
            Use filtros para conferir os produtos que alimentam recomendacoes, similares e rotinas.
          </p>
        </header>

        <section className="grid gap-4 rounded-lg border border-ink/10 bg-white p-5 shadow-soft md:grid-cols-5">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Categoria</span>
            <select
              value={filters.category ?? ""}
              onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value || undefined }))}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm"
            >
              {categories.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "Todas"}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Etapa</span>
            <select
              value={filters.routine_step ?? ""}
              onChange={(event) => setFilters((current) => ({ ...current, routine_step: event.target.value || undefined }))}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm"
            >
              {steps.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "Todas"}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Tag</span>
            <input
              value={filters.tag ?? ""}
              onChange={(event) => setFilters((current) => ({ ...current, tag: event.target.value || undefined }))}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm"
              placeholder="acne"
            />
          </label>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-ink">Preco</span>
            <select
              value={filters.price_range ?? ""}
              onChange={(event) => setFilters((current) => ({ ...current, price_range: event.target.value || undefined }))}
              className="rounded-md border border-ink/15 px-3 py-2 text-sm"
            >
              {prices.map((item) => (
                <option key={item || "all"} value={item}>
                  {item || "Todos"}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-end gap-2 pb-2 text-sm font-medium text-ink">
            <input
              type="checkbox"
              checked={filters.is_active_treatment ?? false}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  is_active_treatment: event.target.checked ? true : undefined,
                }))
              }
            />
            Tratamento ativo
          </label>
        </section>

        {error ? <p className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}
        {loading ? <p className="text-sm text-moss">Carregando catalogo...</p> : null}

        <section className="grid gap-3">
          {!loading && products.length === 0 ? (
            <div className="rounded-lg border border-dashed border-ink/20 bg-white p-8 text-center text-sm text-moss">
              Nenhum produto encontrado com os filtros atuais.
            </div>
          ) : null}
          {products.map((product) => (
            <article key={product.product_id} className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-ink">{product.name}</h2>
                  <p className="text-sm text-moss">{product.brand}</p>
                </div>
                <span className="rounded-md bg-linen px-3 py-1 text-xs font-semibold text-moss">
                  {product.catalog_status}
                </span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {[product.category, product.routine_step, product.price_range, ...product.usage_periods, ...product.tags]
                  .filter(Boolean)
                  .map((item) => (
                    <span key={item} className="rounded-md border border-ink/10 px-2 py-1 text-xs text-moss">
                      {item}
                    </span>
                  ))}
              </div>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
