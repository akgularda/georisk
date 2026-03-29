import { ReportCard } from "@/components/report-card";
import { SectionHeading } from "@/components/section-heading";
import { getAllReports } from "@/lib/content";

export const metadata = {
  title: "Reports",
};

export default async function ReportsPage() {
  const reports = await getAllReports();

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="Reports"
            title="Recent intelligence reporting in the same command shell"
            description="Reports stay readable and web-first, but the surrounding frame now follows the same operational structure used by the board, country, and status routes."
          />
        </div>
      </section>
      <section className="mx-auto max-w-7xl p-8">
        <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
          {reports.map((report) => (
            <ReportCard key={report.slug} report={report} />
          ))}
        </div>
      </section>
    </div>
  );
}
