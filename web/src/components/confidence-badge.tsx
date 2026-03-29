import { getConfidenceLabelClasses } from "@/lib/formatters";
import type { ConfidenceBand } from "@/lib/types";

interface ConfidenceBadgeProps {
  confidenceBand: ConfidenceBand;
}

export function ConfidenceBadge({ confidenceBand }: ConfidenceBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-md px-3 py-1.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] ${getConfidenceLabelClasses(confidenceBand)}`}
    >
      Confidence {confidenceBand}
    </span>
  );
}
