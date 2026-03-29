interface SourceAppendixProps {
  sources: string[];
}

export function SourceAppendix({ sources }: SourceAppendixProps) {
  return (
    <section className="terminal-panel rounded-lg p-6">
      <p className="terminal-label text-accent">Source appendix</p>
      <ul className="mt-4 space-y-2 text-sm text-muted">
        {sources.map((source) => (
          <li key={source}>{source}</li>
        ))}
      </ul>
    </section>
  );
}
