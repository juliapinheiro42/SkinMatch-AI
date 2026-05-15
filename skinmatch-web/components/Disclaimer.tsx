type DisclaimerProps = {
  text?: string;
};

export function Disclaimer({ text }: DisclaimerProps) {
  return (
    <p className="rounded-lg border border-ink/10 bg-mist px-4 py-3 text-sm leading-6 text-moss">
      {text || "Esta analise e uma estimativa educacional e nao substitui orientacao medica ou dermatologica."}
    </p>
  );
}
