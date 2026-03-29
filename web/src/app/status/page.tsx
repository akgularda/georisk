import { SectionHeading } from "@/components/section-heading";
import { getAllReports } from "@/lib/content";
import { formatDateTime, formatProbabilityPercent } from "@/lib/formatters";
import { buildMonitoringWatchItems, getPrimaryCountryLabel, hasPublishableLeader } from "@/lib/monitoring-presentation";
import { getOperationalCountries, getOperationalStatusSummary } from "@/lib/site-data";

export const metadata = {
  title: "System status",
};

export default async function StatusPage() {
  const countries = getOperationalCountries();
  const status = getOperationalStatusSummary();
  const reports = await getAllReports();
  const publishableLeader = hasPublishableLeader(status);
  const focusWatch = publishableLeader ? null : buildMonitoringWatchItems(countries, reports)[0] ?? null;

  return (
    <div className="dashboard-canvas pb-20 md:pb-8">
      <section className="shell-panel border-x-0 border-t-0 px-8 py-10 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <SectionHeading
            eyebrow="System status"
            title="Snapshot freshness, provenance, and fallback state"
            description="This is the trust surface. It makes stale data, fallback activation, baseline usage, and model quality visible without requiring readers to inspect raw artifacts."
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl space-y-8 p-8">
      <div className="grid gap-4 md:grid-cols-4">
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Alert Type</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.alertType}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Primary Target</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.primaryTarget}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">Model Status</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.modelStatus}</p>
        </div>
        <div className="shell-card p-5">
          <p className="command-eyebrow text-[#ff8f82]">No Clear Leader</p>
          <p className="mt-3 text-2xl font-semibold tracking-[-0.05em] text-foreground">{status.noClearLeader ? "Yes" : "No"}</p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Publication</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="command-eyebrow">Source Kind</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.sourceKind}</p>
            </div>
            <div>
              <p className="command-eyebrow">Freshness</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.freshnessTier}</p>
            </div>
            <div>
              <p className="command-eyebrow">Published At</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.publishedAt ? formatDateTime(status.publishedAt) : "Unavailable"}</p>
            </div>
            <div>
              <p className="command-eyebrow">Forecast As Of</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.forecastAsOf ?? "Unavailable"}</p>
            </div>
            <div>
              <p className="command-eyebrow">Coverage</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.coverageCount} countries</p>
            </div>
            <div>
              <p className="command-eyebrow">{getPrimaryCountryLabel(status)}</p>
              <p className="mt-2 text-sm font-semibold text-foreground">
                {publishableLeader ? status.leadCountryName ?? "Unavailable" : focusWatch?.country.name ?? "Unavailable"}
              </p>
            </div>
          </div>
          <p className="mt-4 text-sm leading-7 text-muted">{status.message ?? "Preferred published snapshot is active."}</p>
        </div>

        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Threshold Policy</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="command-eyebrow">Publish Top N</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{status.thresholdPolicy.publishTopN}</p>
            </div>
            <div>
              <p className="command-eyebrow">Publish Threshold</p>
              <p className="mt-2 text-sm font-semibold text-foreground">
                {status.publishThreshold == null ? "Unavailable" : formatProbabilityPercent(status.publishThreshold)}
              </p>
            </div>
            <div>
              <p className="command-eyebrow">Operating</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{formatProbabilityPercent(status.thresholdPolicy.operatingThreshold)}</p>
            </div>
            <div>
              <p className="command-eyebrow">Warning</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{formatProbabilityPercent(status.thresholdPolicy.warningThreshold)}</p>
            </div>
            <div>
              <p className="command-eyebrow">Alert</p>
              <p className="mt-2 text-sm font-semibold text-foreground">{formatProbabilityPercent(status.thresholdPolicy.alertThreshold)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Model Provenance</p>
          <div className="mt-4 space-y-3 text-sm leading-7 text-muted">
            <p>Model: <span className="font-semibold text-foreground">{status.modelName}</span></p>
            <p>Version: <span className="font-semibold text-foreground">{status.modelVersion}</span></p>
            <p>Structural prior active: <span className="font-semibold text-foreground">{status.structuralPriorActive ? "Yes" : "No"}</span></p>
            <p>Structural prior run: <span className="font-semibold text-foreground">{status.structuralPriorRunName ?? "Unavailable"}</span></p>
            <p>Structural artifact freshness: <span className="font-semibold text-foreground">{status.structuralPriorCompletedAt ? formatDateTime(status.structuralPriorCompletedAt) : "Unavailable"}</span></p>
            <p>Primary backtest model: <span className="font-semibold text-foreground">{status.primaryModel}</span></p>
            <p>Top backtest model: <span className="font-semibold text-foreground">{status.topModelName ?? "Unavailable"}</span></p>
            <p>Calibration method: <span className="font-semibold text-foreground">{status.calibrationMethod ?? "Unavailable"}</span></p>
          </div>
        </div>

        <div className="shell-card p-6">
          <p className="command-eyebrow text-[#ff8f82]">Operating Metrics</p>
          <div className="mt-4 space-y-3 text-sm leading-7 text-muted">
            <p>Episode recall: <span className="font-semibold text-foreground">{status.episodeRecall == null ? "Unavailable" : formatProbabilityPercent(status.episodeRecall)}</span></p>
            <p>Recall@5: <span className="font-semibold text-foreground">{status.recallAt5 == null ? "Unavailable" : formatProbabilityPercent(status.recallAt5)}</span></p>
            <p>Recall@10: <span className="font-semibold text-foreground">{status.recallAt10 == null ? "Unavailable" : formatProbabilityPercent(status.recallAt10)}</span></p>
            <p>False alerts per true alert: <span className="font-semibold text-foreground">{status.falseAlertsPerTrueAlert ?? "Unavailable"}</span></p>
            <p>No clear leader rate: <span className="font-semibold text-foreground">{status.noClearLeaderRate == null ? "Unavailable" : formatProbabilityPercent(status.noClearLeaderRate)}</span></p>
            <p>PR AUC delta: <span className="font-semibold text-foreground">{status.deltaPrAuc ?? "Unavailable"}</span></p>
            <p>ROC AUC delta: <span className="font-semibold text-foreground">{status.deltaRocAuc ?? "Unavailable"}</span></p>
            <p>F1 delta: <span className="font-semibold text-foreground">{status.deltaF1 ?? "Unavailable"}</span></p>
            <p>Brier delta: <span className="font-semibold text-foreground">{status.deltaBrierScore ?? "Unavailable"}</span></p>
          </div>
        </div>
      </div>
      </section>
    </div>
  );
}
