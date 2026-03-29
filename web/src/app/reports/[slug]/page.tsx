import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { MethodologyNote } from "@/components/methodology-note";
import { ReportToc } from "@/components/report-toc";
import { SourceAppendix } from "@/components/source-appendix";
import { formatDate, formatDateTime } from "@/lib/formatters";
import { getAllReports, getReportBySlug, getReportSlugs } from "@/lib/content";
import { siteConfig } from "@/lib/site";

interface ReportPageProps {
  params: Promise<{ slug: string }>;
}

export const dynamicParams = false;

export async function generateStaticParams() {
  return getReportSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: ReportPageProps): Promise<Metadata> {
  const { slug } = await params;
  const report = await getReportBySlug(slug);
  if (!report) {
    return {};
  }
  return {
    title: report.frontmatter.title,
    description: report.frontmatter.summary,
  };
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { slug } = await params;
  const report = await getReportBySlug(slug);
  if (!report) {
    notFound();
  }

  const { frontmatter, Content } = report;
  const relatedReports = (await getAllReports()).filter(
    (candidate) => candidate.slug !== frontmatter.slug && candidate.region === frontmatter.region,
  );

  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: frontmatter.title,
    description: frontmatter.summary,
    datePublished: frontmatter.date,
    dateModified: frontmatter.updatedAt,
    author: frontmatter.authors.map((author) => ({ "@type": "Person", name: author })),
    publisher: {
      "@type": "Organization",
      name: siteConfig.name,
    },
  };

  return (
    <div className="mx-auto max-w-[1500px] px-5 py-12 sm:px-8 lg:px-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(articleJsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <div className="grid gap-8 lg:grid-cols-[0.74fr_0.26fr]">
        <article className="space-y-8">
          <header className="terminal-panel space-y-5 rounded-lg p-7">
            <div className="flex flex-wrap items-center gap-3 text-[0.68rem] uppercase tracking-[0.24em] text-muted">
              <span>{frontmatter.region}</span>
              <span>{frontmatter.heroMetric}</span>
              <span>{frontmatter.horizon}</span>
            </div>
            <h1 className="max-w-4xl text-4xl font-semibold tracking-[-0.05em] text-foreground sm:text-5xl">
              {frontmatter.title}
            </h1>
            <p className="max-w-3xl text-lg leading-8 text-muted">{frontmatter.summary}</p>
            <div className="grid gap-4 text-sm text-muted sm:grid-cols-2">
              <p>Published {formatDate(frontmatter.date)}</p>
              <p>Updated {formatDateTime(frontmatter.updatedAt)}</p>
              <p>Authors: {frontmatter.authors.join(", ")}</p>
              <p>Forecast version: {frontmatter.forecastVersion}</p>
            </div>
          </header>

          <div className="terminal-panel rounded-lg p-7">
            <div className="report-prose">
              <Content />
            </div>
          </div>

          <SourceAppendix sources={frontmatter.sources} />
          <MethodologyNote />

          {relatedReports.length > 0 ? (
            <section className="space-y-4">
              <p className="terminal-label text-accent">Related reports</p>
              <div className="grid gap-4 md:grid-cols-2">
                {relatedReports.slice(0, 2).map((candidate) => (
                  <a key={candidate.slug} href={`/reports/${candidate.slug}`} className="terminal-panel rounded-lg p-5 hover:border-accent/20">
                    <h2 className="text-xl font-semibold tracking-[-0.03em] text-foreground">{candidate.title}</h2>
                    <p className="mt-3 text-sm leading-7 text-muted">{candidate.summary}</p>
                  </a>
                ))}
              </div>
            </section>
          ) : null}
        </article>
        <ReportToc items={frontmatter.toc} />
      </div>
    </div>
  );
}
