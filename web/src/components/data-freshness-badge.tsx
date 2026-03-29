interface DataFreshnessBadgeProps {
  freshness: string;
}

export function DataFreshnessBadge({ freshness }: DataFreshnessBadgeProps) {
  return (
    <span className="inline-flex rounded-md border border-border bg-surface-muted px-3 py-1.5 text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-muted">
      Freshness {freshness}
    </span>
  );
}
