import Link from "next/link";

interface MethodologyNoteProps {
  compact?: boolean;
}

export function MethodologyNote({ compact = false }: MethodologyNoteProps) {
  return (
    <aside className={`command-panel-muted ${compact ? "p-4" : "p-6"}`}>
      <p className="command-eyebrow text-[#ff8f82]">Methodology note</p>
      <p className="mt-3 text-sm leading-7 text-muted">
        Scores on the live site are published probabilities from the current snapshot bundle, not decorative severity
        numbers. Freshness, provenance, baseline fallback, and backtest deltas should stay visible beside the forecast.
      </p>
      <Link href="/methodology/model" className="mt-4 inline-flex text-sm font-semibold text-foreground hover:text-accent">
        {"Review model framing ->"}
      </Link>
    </aside>
  );
}
