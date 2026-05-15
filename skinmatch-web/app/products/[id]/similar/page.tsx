"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getSimilarProducts } from "@/lib/api";
import type { SimilarProduct } from "@/types/analysis";

export default function SimilarProductsPage() {
  const params = useParams<{ id: string }>();
  const [products, setProducts] = useState<SimilarProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSimilarProducts(params.id)
      .then(setProducts)
      .catch(() => setError("Nao foi possivel carregar produtos similares."))
      .finally(() => setLoading(false));
  }, [params.id]);

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-6">
        <header className="grid gap-2">
          <h1 className="text-3xl font-semibold text-ink">Produtos similares</h1>
          <p className="text-sm leading-6 text-moss">
            Similaridade calculada sobre embeddings da formula normalizada.
          </p>
        </header>

        {loading ? <section className="rounded-lg border border-ink/10 bg-white p-6 text-sm text-moss shadow-soft">Carregando similares...</section> : null}
        {error ? <section className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800">{error}</section> : null}

        {!loading && !error && products.length === 0 ? (
          <section className="rounded-lg border border-dashed border-ink/20 bg-white/70 p-8 text-center shadow-soft">
            <h2 className="text-lg font-semibold text-ink">Sem similares ainda</h2>
            <p className="mt-2 text-sm text-moss">Analise mais produtos para alimentar a base de formulas.</p>
          </section>
        ) : null}

        <div className="grid gap-4">
          {products.map((product) => (
            <article key={product.product_id} className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-ink">{product.name}</h2>
                  <p className="mt-1 text-sm text-moss">{product.brand}</p>
                </div>
                <strong className="text-2xl font-semibold text-ink">{product.similarity}%</strong>
              </div>
              <Link
                href="/"
                className="mt-5 inline-flex rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-moss"
              >
                Analisar este produto
              </Link>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
