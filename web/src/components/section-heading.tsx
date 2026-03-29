interface SectionHeadingProps {
  eyebrow: string;
  title: string;
  description?: string;
}

export function SectionHeading({ eyebrow, title, description }: SectionHeadingProps) {
  return (
    <div className="space-y-4">
      <p className="command-eyebrow text-primary">{eyebrow}</p>
      <h2 className="font-headline max-w-4xl text-4xl font-bold tracking-[-0.06em] text-foreground sm:text-[3rem]">{title}</h2>
      {description ? <p className="max-w-3xl text-base leading-8 text-[rgba(218,226,253,0.74)]">{description}</p> : null}
    </div>
  );
}
