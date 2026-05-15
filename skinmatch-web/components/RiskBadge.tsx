type RiskBadgeProps = {
  label: string;
  tone: "low" | "medium" | "high";
};

const toneStyles = {
  low: "bg-emerald-50 text-emerald-800 ring-emerald-200",
  medium: "bg-amber-50 text-amber-800 ring-amber-200",
  high: "bg-rose-50 text-rose-800 ring-rose-200",
};

export function RiskBadge({ label, tone }: RiskBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ring-1 ${toneStyles[tone]}`}>
      {label}
    </span>
  );
}
