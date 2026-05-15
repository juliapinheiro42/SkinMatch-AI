"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { type Resolver, useForm } from "react-hook-form";
import { AnalysisResult } from "@/components/AnalysisResult";
import { FormulaForm } from "@/components/FormulaForm";
import { Recommendations } from "@/components/Recommendations";
import { SkinProfileForm } from "@/components/SkinProfileForm";
import { analyzeFormula, extractFormulaFromImage } from "@/lib/api";
import { analysisFormSchema, type AnalysisFormInput, type AnalysisFormValues } from "@/lib/schemas";
import type { AnalysisRequest, AnalysisResponse } from "@/types/analysis";

const defaultValues: Partial<AnalysisFormInput> = {
  sensitive_skin: false,
  acne_prone: false,
  barrier_compromised: false,
  known_triggers: "",
  tolerated_ingredients: "",
};

function toPayload(values: AnalysisFormValues): AnalysisRequest {
  return {
    skin_profile: {
      skin_type: values.skin_type,
      sensitive_skin: values.sensitive_skin,
      acne_prone: values.acne_prone,
      barrier_compromised: values.barrier_compromised,
      known_triggers: values.known_triggers,
      tolerated_ingredients: values.tolerated_ingredients,
    },
    main_goal: values.main_goal,
    product_name: values.product_name || undefined,
    brand: values.brand || undefined,
    raw_ingredient_list: values.raw_ingredient_list,
  };
}

export default function Home() {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [lastPayload, setLastPayload] = useState<AnalysisRequest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrText, setOcrText] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AnalysisFormInput, unknown, AnalysisFormValues>({
    resolver: zodResolver(analysisFormSchema) as Resolver<AnalysisFormInput, unknown, AnalysisFormValues>,
    defaultValues,
  });

  async function onSubmit(values: AnalysisFormValues) {
    setError(null);
    setResult(null);

    try {
      const payload = toPayload(values);
      const analysis = await analyzeFormula(payload);
      setLastPayload(payload);
      setResult(analysis);
    } catch {
      setError("Nao foi possivel analisar a formula. Verifique se o backend esta rodando.");
    }
  }

  async function onImageSelected(file: File | undefined) {
    if (!file) return;

    setError(null);
    setOcrText(null);
    setOcrLoading(true);
    setImagePreview(URL.createObjectURL(file));

    try {
      const extracted = await extractFormulaFromImage(file);
      setOcrText(extracted.extracted_text);
      if (extracted.cleaned_ingredient_list) {
        setValue("raw_ingredient_list", extracted.cleaned_ingredient_list, { shouldValidate: true });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Nao foi possivel ler a imagem.";
      setError(`${message} Voce ainda pode colar a formula manualmente.`);
    } finally {
      setOcrLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-8">
        <header className="grid gap-3 py-4">
          <p className="text-sm font-semibold uppercase tracking-wide text-sage">MVP deterministico com historico</p>
          <h1 className="max-w-3xl text-4xl font-semibold text-ink sm:text-5xl">SkinMatch AI</h1>
          <p className="max-w-3xl text-lg leading-8 text-moss">
            Analise a compatibilidade de uma formula de skincare com o seu perfil de pele
          </p>
        </header>

        <div className="grid gap-8 xl:grid-cols-[minmax(0,0.95fr)_minmax(420px,1.05fr)]">
          <form className="grid gap-6" onSubmit={handleSubmit(onSubmit)}>
            <SkinProfileForm register={register} errors={errors} />
            <FormulaForm register={register} errors={errors} />

            <section className="rounded-lg border border-ink/10 bg-white p-6 shadow-soft">
              <h2 className="text-lg font-semibold text-ink">Ou envie uma foto do rotulo</h2>
              <div className="mt-5 grid gap-4">
                <label className="grid gap-2">
                  <span className="text-sm font-medium text-ink">Imagem do rotulo</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="rounded-md border border-ink/15 bg-white px-3 py-3 text-sm text-ink file:mr-4 file:rounded-md file:border-0 file:bg-ink file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
                    onChange={(event) => onImageSelected(event.target.files?.[0])}
                  />
                </label>
                {imagePreview ? (
                  <img src={imagePreview} alt="Preview do rotulo" className="max-h-56 w-full rounded-md object-cover" />
                ) : null}
                {ocrLoading ? <p className="text-sm text-moss">Lendo imagem...</p> : null}
                {ocrText ? (
                  <details className="rounded-md bg-linen px-4 py-3 text-sm text-moss">
                    <summary className="cursor-pointer font-semibold text-ink">Texto extraido</summary>
                    <p className="mt-2 whitespace-pre-wrap leading-6">{ocrText}</p>
                  </details>
                ) : null}
              </div>
            </section>

            {error ? (
              <p className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
            ) : null}

            <button
              type="submit"
              disabled={isSubmitting}
              className="h-12 rounded-md bg-ink px-5 text-sm font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Analisando formula..." : "Analisar formula"}
            </button>
          </form>

          <aside className="min-h-[28rem]">
            {result ? (
              <div className="grid gap-6">
                <AnalysisResult result={result} />
                {lastPayload ? <Recommendations analysisPayload={lastPayload} /> : null}
              </div>
            ) : (
              <section className="flex min-h-[28rem] items-center justify-center rounded-lg border border-dashed border-ink/20 bg-white/70 p-8 text-center shadow-soft">
                <div className="max-w-sm">
                  <h2 className="text-xl font-semibold text-ink">Resultado</h2>
                  <p className="mt-3 text-sm leading-6 text-moss">
                    Preencha seu perfil, cole a formula INCI e envie para receber uma estimativa educacional de compatibilidade.
                  </p>
                </div>
              </section>
            )}
          </aside>
        </div>
      </div>
    </main>
  );
}
