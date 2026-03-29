import type { DriverItem } from "@/lib/types";

interface DriverListProps {
  drivers: DriverItem[];
}

export function DriverList({ drivers }: DriverListProps) {
  return (
    <div className="grid gap-4">
      {drivers.map((driver) => (
        <article key={driver.title} className="terminal-panel rounded-lg p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-lg font-semibold tracking-[-0.03em] text-foreground">{driver.title}</h3>
            <span className="rounded-md border border-border bg-surface-muted px-3 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-accent">
              {driver.intensity}
            </span>
          </div>
          <p className="text-sm leading-7 text-muted">{driver.detail}</p>
        </article>
      ))}
    </div>
  );
}
