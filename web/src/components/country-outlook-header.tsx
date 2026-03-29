import { ConfidenceBadge } from "@/components/confidence-badge";
import { CountryPulseGraphic } from "@/components/country-pulse-graphic";
import { DataFreshnessBadge } from "@/components/data-freshness-badge";
import { RiskBadge } from "@/components/risk-badge";
import { formatDateTime } from "@/lib/formatters";
import type { CountryProfile } from "@/lib/types";

interface CountryOutlookHeaderProps {
  country: CountryProfile;
}

export function CountryOutlookHeader({ country }: CountryOutlookHeaderProps) {
  return (
    <section className="mx-auto grid max-w-[1500px] gap-6 px-5 py-10 sm:px-8 lg:grid-cols-[0.92fr_1.08fr_0.85fr] lg:px-10 lg:py-14">
      <div className="terminal-panel section-fade-in rounded-lg p-6">
        <p className="terminal-label text-accent">{country.region} dossier</p>
        <div className="space-y-4">
          <h1 className="text-4xl font-semibold tracking-[-0.06em] text-foreground sm:text-5xl">{country.name}</h1>
          <p className="max-w-xl text-base leading-8 text-muted">{country.executiveSummary}</p>
        </div>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <RiskBadge category={country.riskCategory} score={country.riskScore} />
          <ConfidenceBadge confidenceBand={country.confidenceBand} />
          <DataFreshnessBadge freshness={country.currentSignals[2]?.value ?? "same day"} />
        </div>
        <p className="mt-6 text-sm leading-7 text-muted">{country.sourceNote}</p>
      </div>

      <CountryPulseGraphic
        country={country.shapeKey}
        title={country.name}
        size="dossier"
        label={country.name}
        className="section-fade-in [animation-delay:90ms]"
      />

      <aside className="terminal-panel-muted section-fade-in rounded-lg p-6 [animation-delay:160ms]">
        <p className="terminal-label text-accent">Operational metadata</p>
        <dl className="mt-5 grid gap-5">
          <div>
            <dt className="terminal-label">Forecast horizon</dt>
            <dd className="mt-2 text-base font-semibold text-foreground">{country.horizon}</dd>
          </div>
          <div>
            <dt className="terminal-label">Last updated</dt>
            <dd className="mt-2 text-sm font-semibold text-foreground">{formatDateTime(country.updatedAt)}</dd>
          </div>
          <div>
            <dt className="terminal-label">Forecast version</dt>
            <dd className="mt-2 text-sm font-semibold text-foreground">{country.forecastVersion}</dd>
          </div>
          <div>
            <dt className="terminal-label">Model version</dt>
            <dd className="mt-2 text-sm font-semibold text-foreground">{country.modelVersion}</dd>
          </div>
          <div>
            <dt className="terminal-label">Current read</dt>
            <dd className="mt-2 text-sm leading-7 text-muted">{country.summary}</dd>
          </div>
        </dl>
      </aside>
    </section>
  );
}
