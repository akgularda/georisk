import type { TimelineEvent } from "@/lib/types";

interface TimelineListProps {
  events: TimelineEvent[];
}

export function TimelineList({ events }: TimelineListProps) {
  return (
    <div className="relative space-y-5 before:absolute before:bottom-0 before:left-[8px] before:top-2 before:w-px before:bg-border">
      {events.map((event) => (
        <article key={`${event.date}-${event.label}`} className="relative pl-8">
          <span className="absolute left-0 top-2 h-4 w-4 rounded-full border border-accent/20 bg-accent-soft" />
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">{event.date}</p>
            <span className="rounded-md border border-border bg-surface-muted px-3 py-1 text-[0.68rem] uppercase tracking-[0.2em] text-muted">
              {event.signalType}
            </span>
          </div>
          <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-foreground">{event.label}</h3>
          <p className="mt-2 text-sm leading-7 text-muted">{event.summary}</p>
        </article>
      ))}
    </div>
  );
}
