import { AppIcon } from "@/components/app-icon";
import Link from "next/link";
import { formatDate } from "@/lib/formatters";
import { getReportConflictLabel } from "@/lib/monitoring-presentation";
import type { ReportFrontmatter } from "@/lib/types";

interface ReportCardProps {
  report: ReportFrontmatter;
}

function visualTone(report: ReportFrontmatter) {
  const signature = `${report.region}-${report.tags[0] ?? "report"}-${report.slug}`.toLowerCase();
  if (signature.includes("econ") || signature.includes("market")) {
    return "report-visual-amber";
  }
  if (signature.includes("cyber") || signature.includes("tech") || signature.includes("data")) {
    return "report-visual-blue";
  }
  return "report-visual-red";
}

export function ReportCard({ report }: ReportCardProps) {
  const tone = visualTone(report);
  const conflictLabel = getReportConflictLabel(report);

  return (
    <article className="report-card-shell group overflow-hidden">
      <div className={`report-visual ${tone} aspect-video`}>
        <div className="absolute top-3 right-3 z-10 rounded-sm bg-[rgba(147,0,10,0.92)] px-2 py-1 text-[8px] font-bold uppercase tracking-[0.18em] text-[#ffdad6]">
          {report.tags[0] ?? "Intel"}
        </div>
      </div>
      <div className="p-4">
        <div className="mb-1 text-[9px] font-bold uppercase tracking-[0.18em] text-tertiary">{report.region}</div>
        <h3 className="report-card-title text-sm font-bold leading-tight text-foreground transition-colors group-hover:text-primary">
          {report.title}
        </h3>
        <div className="mt-3 text-[9px] font-bold uppercase tracking-[0.18em] text-[rgba(218,226,253,0.5)]">
          Predicted conflict
        </div>
        <div className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-[rgba(218,226,253,0.82)]">
          {conflictLabel}
        </div>
        <p className="mt-3 text-sm leading-6 text-[rgba(218,226,253,0.72)]">{report.summary}</p>
        <div className="mt-4 flex items-center justify-between border-t border-[rgba(69,70,77,0.16)] pt-3">
          <span className="text-[10px] text-[rgba(218,226,253,0.6)]">{formatDate(report.date)}</span>
          <Link href={`/reports/${report.slug}`} className="text-[rgba(218,226,253,0.68)]">
            <AppIcon name="arrow_forward" className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </article>
  );
}
