import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getMethodologyPageBySlug, getMethodologySlugs } from "@/lib/content";

interface MethodologyPageProps {
  params: Promise<{ slug: string }>;
}

export const dynamicParams = false;

export async function generateStaticParams() {
  return getMethodologySlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: MethodologyPageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await getMethodologyPageBySlug(slug);
  if (!page) {
    return {};
  }
  return {
    title: page.frontmatter.title,
    description: page.frontmatter.summary,
  };
}

export default async function MethodologyPage({ params }: MethodologyPageProps) {
  const { slug } = await params;
  const page = await getMethodologyPageBySlug(slug);
  if (!page) {
    notFound();
  }

  const { frontmatter, Content } = page;

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-5 py-12 sm:px-8 lg:px-10">
      <header className="terminal-panel rounded-lg p-7">
        <p className="terminal-label text-accent">Methodology</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-[-0.05em] text-foreground">{frontmatter.title}</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted">{frontmatter.summary}</p>
      </header>
      <article className="terminal-panel rounded-lg p-7">
        <div className="report-prose">
          <Content />
        </div>
      </article>
    </div>
  );
}
