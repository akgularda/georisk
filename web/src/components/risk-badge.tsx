import { getRiskToneClasses } from "@/lib/formatters";
import type { RiskCategory } from "@/lib/types";

interface RiskBadgeProps {
  category: RiskCategory;
  score: number;
}

export function RiskBadge({ category, score }: RiskBadgeProps) {
  return (
    <div
      className={`inline-flex items-center rounded-md border px-3 py-1.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] ${getRiskToneClasses(category)}`}
    >
      {category} {score}
    </div>
  );
}
