import type { ScenarioItem } from "@/lib/types";

interface ScenarioGridProps {
  scenarios: ScenarioItem[];
}

export function ScenarioGrid({ scenarios }: ScenarioGridProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {scenarios.map((scenario) => (
        <article key={scenario.label} className="terminal-panel rounded-lg p-5">
          <p className="terminal-label text-accent">{scenario.label}</p>
          <p className="mt-3 text-sm leading-7 text-foreground">{scenario.summary}</p>
          <p className="mt-4 text-xs uppercase tracking-[0.18em] text-muted">{scenario.probabilityNote}</p>
        </article>
      ))}
    </div>
  );
}
