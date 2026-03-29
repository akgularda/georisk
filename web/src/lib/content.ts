import type { ComponentType } from "react";
import type { MethodologyFrontmatter, ReportFrontmatter } from "@/lib/types";

type MDXModule<TFrontmatter> = {
  default: ComponentType;
  frontmatter: TFrontmatter;
};

const reportRegistry = [
  { slug: "iran-israel-escalation-watch", load: () => import("../../content/reports/iran-israel-escalation-watch.mdx") },
  { slug: "sudan-corridor-pressure", load: () => import("../../content/reports/sudan-corridor-pressure.mdx") },
  { slug: "ukraine-black-sea-watch", load: () => import("../../content/reports/ukraine-black-sea-watch.mdx") },
  { slug: "syria-border-fragility-note", load: () => import("../../content/reports/syria-border-fragility-note.mdx") },
] as const;

const methodologyRegistry = [
  { slug: "data", load: () => import("../../content/methodology/data.mdx") },
  { slug: "model", load: () => import("../../content/methodology/model.mdx") },
  { slug: "backtesting", load: () => import("../../content/methodology/backtesting.mdx") },
] as const;

export async function getAllReports(): Promise<ReportFrontmatter[]> {
  const reports = await Promise.all(
    reportRegistry.map(async ({ load }) => {
      const mdxEntry = (await load()) as MDXModule<ReportFrontmatter>;
      return mdxEntry.frontmatter;
    }),
  );
  return reports.filter((report) => !report.draft).sort((left, right) => right.date.localeCompare(left.date));
}

export async function getReportBySlug(
  slug: string,
): Promise<{ frontmatter: ReportFrontmatter; Content: ComponentType } | undefined> {
  const entry = reportRegistry.find((report) => report.slug === slug);
  if (!entry) {
    return undefined;
  }
  const mdxEntry = (await entry.load()) as MDXModule<ReportFrontmatter>;
  return { frontmatter: mdxEntry.frontmatter, Content: mdxEntry.default };
}

export function getReportSlugs(): string[] {
  return reportRegistry.map((report) => report.slug);
}

export async function getAllMethodologyPages(): Promise<MethodologyFrontmatter[]> {
  const pages = await Promise.all(
    methodologyRegistry.map(async ({ load }) => {
      const mdxEntry = (await load()) as MDXModule<MethodologyFrontmatter>;
      return mdxEntry.frontmatter;
    }),
  );
  return pages.filter((page) => !page.draft).sort((left, right) => left.title.localeCompare(right.title));
}

export async function getMethodologyPageBySlug(
  slug: string,
): Promise<{ frontmatter: MethodologyFrontmatter; Content: ComponentType } | undefined> {
  const entry = methodologyRegistry.find((page) => page.slug === slug);
  if (!entry) {
    return undefined;
  }
  const mdxEntry = (await entry.load()) as MDXModule<MethodologyFrontmatter>;
  return { frontmatter: mdxEntry.frontmatter, Content: mdxEntry.default };
}

export function getMethodologySlugs(): string[] {
  return methodologyRegistry.map((page) => page.slug);
}
