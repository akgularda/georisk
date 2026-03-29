"use client";

import Link from "next/link";
import { startTransition, useDeferredValue, useState } from "react";
import { formatProbabilityDelta, formatProbabilityPercent, getAlertStatusClasses, getAlertStatusLabel } from "@/lib/formatters";
import type { OperationalCountry } from "@/lib/types";

interface MonitorTableProps {
  countries: OperationalCountry[];
  limit?: number;
  showControls?: boolean;
}

export function MonitorTable({ countries, limit, showControls = true }: MonitorTableProps) {
  const [region, setRegion] = useState("All");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");

  const deferredRegion = useDeferredValue(region);
  const deferredStatus = useDeferredValue(status);
  const deferredQuery = useDeferredValue(query).trim().toLowerCase();

  const regions = ["All", ...new Set(countries.map((country) => country.region))];
  const statuses = ["All", ...new Set(countries.map((country) => getAlertStatusLabel(country.alertStatus)))];

  const filteredCountries = countries
    .filter((country) => deferredRegion === "All" || country.region === deferredRegion)
    .filter((country) => deferredStatus === "All" || getAlertStatusLabel(country.alertStatus) === deferredStatus)
    .filter(
      (country) =>
        deferredQuery.length === 0 ||
        country.name.toLowerCase().includes(deferredQuery) ||
        country.summary.toLowerCase().includes(deferredQuery),
    );

  const visibleCountries = typeof limit === "number" ? filteredCountries.slice(0, limit) : filteredCountries;

  return (
    <div className="space-y-4">
      {showControls ? (
        <div className="command-panel p-4">
          <div className="grid gap-4 md:grid-cols-[0.95fr_0.55fr_0.55fr]">
            <label className="grid gap-2">
              <span className="command-eyebrow">Search</span>
              <input
                value={query}
                onChange={(event) => startTransition(() => setQuery(event.target.value))}
                placeholder="Australia, corridor, ACLED..."
                className="command-input"
              />
            </label>
            <label className="grid gap-2">
              <span className="command-eyebrow">Region</span>
              <select value={region} onChange={(event) => startTransition(() => setRegion(event.target.value))} className="command-input">
                {regions.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2">
              <span className="command-eyebrow">Threshold State</span>
              <select value={status} onChange={(event) => startTransition(() => setStatus(event.target.value))} className="command-input">
                {statuses.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      ) : null}

      <div className="command-panel overflow-x-auto">
        <table className="command-table min-w-[1080px] w-full border-collapse">
          <thead>
            <tr className="border-b border-border/80 text-left">
              <th className="px-4 py-4 command-eyebrow">Rank</th>
              <th className="px-4 py-4 command-eyebrow">Country</th>
              <th className="px-4 py-4 command-eyebrow">30d Probability</th>
              <th className="px-4 py-4 command-eyebrow">Weekly Move</th>
              <th className="px-4 py-4 command-eyebrow">Threshold State</th>
              <th className="px-4 py-4 command-eyebrow">Freshness</th>
              <th className="px-4 py-4 command-eyebrow">Operational Read</th>
            </tr>
          </thead>
          <tbody>
            {visibleCountries.map((country) => (
              <tr key={country.iso3} className="border-b border-border/60 align-top last:border-b-0">
                <td className="px-4 py-4 text-sm font-semibold text-foreground">{String(country.rank).padStart(2, "0")}</td>
                <td className="px-4 py-4">
                  <Link href={`/countries/${country.slug}`} className="text-lg font-semibold tracking-[-0.03em] text-foreground hover:text-accent">
                    {country.name}
                  </Link>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-muted">
                    {country.iso3} / {country.region}
                  </p>
                </td>
                <td className="px-4 py-4">
                  <p className="text-lg font-semibold text-foreground">{formatProbabilityPercent(country.probability)}</p>
                </td>
                <td className="px-4 py-4">
                  <p className={country.delta > 0 ? "font-semibold text-[#ff8f82]" : country.delta < 0 ? "font-semibold text-[#8bc3ff]" : "text-muted"}>
                    {formatProbabilityDelta(country.delta)}
                  </p>
                </td>
                <td className="px-4 py-4">
                  <span className={`inline-flex rounded-full border px-3 py-1.5 text-[0.7rem] font-semibold uppercase tracking-[0.18em] ${getAlertStatusClasses(country.alertStatus)}`}>
                    {getAlertStatusLabel(country.alertStatus)}
                  </span>
                </td>
                <td className="px-4 py-4 text-sm uppercase tracking-[0.18em] text-muted">{country.freshnessTier}</td>
                <td className="px-4 py-4 text-sm leading-7 text-muted">{country.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
