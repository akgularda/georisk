interface ReportTocProps {
  items: { id: string; label: string }[];
}

export function ReportToc({ items }: ReportTocProps) {
  return (
    <aside className="terminal-panel-muted print-hidden rounded-lg p-5 lg:sticky lg:top-24">
      <p className="terminal-label text-accent">On this page</p>
      <nav className="mt-4 space-y-3 text-sm text-muted">
        {items.map((item) => (
          <a key={item.id} href={`#${item.id}`} className="block transition-colors hover:text-foreground">
            {item.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}
