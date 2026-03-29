"use client";

import Link from "next/link";
import { startTransition, useDeferredValue, useState } from "react";
import { formatProbabilityDelta, formatProbabilityPercent, getAlertStatusClasses, getAlertStatusLabel } from "@/lib/formatters";
import type { OperationalForecastRow } from "@/lib/types";

interface ForecastExplorerProps {
  rows: OperationalForecastRow[];
}

type SortMode = "rank" | "probability" | "delta";

export function ForecastExplorer({ rows }: ForecastExplorerProps) {
  const [region, setRegion] = useState("All");
  const [thresholdState, setThresholdState] = useState("All");
  const [sortMode, setSortMode] = useState<SortMode>("rank");

  const deferredRegion = useDeferredValue(region);
  const deferredThresholdState = useDeferredValue(thresholdState);
  const deferredSortMode = useDeferredValue(sortMode);

  const regions = ["All", ...new Set(rows.map((row) => row.region))];
  const thresholdStates = ["All", ...new Set(rows.map((row) => getAlertStatusLabel(row.alertStatus)))];

  const filteredRows = rows
    .filter((row) => deferredRegion === "All" || row.region === deferredRegion)
    .filter((row) => deferredThresholdState === "All" || getAlertStatusLabel(row.alertStatus) === deferredThresholdState)
    .sort((left, right) => {
      if (deferredSortMode === "probability") {
        return right.probability - left.probability || left.rank - right.rank;
      }
      if (deferredSortMode === "delta") {
        return right.delta - left.delta || left.rank - right.rank;
      }
      return left.rank - right.rank || right.probability - left.probability;
    });

  return (
    <div className="space-y-4">
      <div className="command-panel p-4">
        <div className="grid gap-4 md:grid-cols-3">
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
            <select
              value={thresholdState}
              onChange={(event) => startTransition(() => setThresholdState(event.target.value))}
              className="command-input"
            >
              {thresholdStates.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2">
            <span className="command-eyebrow">Sort</span>
            <select value={sortMode} onChange={(event) => startTransition(() => setSortMode(event.target.value as SortMode))} className="command-input">
              <option value="rank">Published rank</option>
              <option value="probability">Highest probability</option>
              <option value="delta">Largest move</option>
            </select>
          </label>
        </div>
      </div>

      <div className="command-panel overflow-x-auto">
        <table className="command-table min-w-[1120px] w-full border-collapse">
          <thead>
            <tr className="border-b border-border/80 text-left">
              <th className="px-4 py-4 command-eyebrow">Rank</th>
              <th className="px-4 py-4 command-eyebrow">Country</th>
              <th className="px-4 py-4 command-eyebrow">30d Probability</th>
              <th className="px-4 py-4 command-eyebrow">Weekly Move</th>
              <th className="px-4 py-4 command-eyebrow">Threshold State</th>
              <th className="px-4 py-4 command-eyebrow">Top Drivers</th>
              <th className="px-4 py-4 command-eyebrow">Snapshot Date</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.iso3} className="border-b border-border/60 align-top last:border-b-0">
                <td className="px-4 py-4 text-sm font-semibold text-foreground">{String(row.rank).padStart(2, "0")}</td>
                <td className="px-4 py-4">
                  <Link href={`/countries/${row.slug}`} className="text-lg font-semibold tracking-[-0.03em] text-foreground hover:text-accent">
                    {row.country}
                  </Link>
                  <p className="mt-1 text-xs uppercase tracking-[0.18em] text-muted">
                    {row.iso3} / {row.region}
                  </p>
                </td>
                <td className="px-4 py-4 text-lg font-semibold text-foreground">{formatProbabilityPercent(row.probability)}</td>
                <td className="px-4 py-4">
                  <span className={row.delta > 0 ? "font-semibold text-[#ff8f82]" : row.delta < 0 ? "font-semibold text-[#8bc3ff]" : "text-muted"}>
                    {formatProbabilityDelta(row.delta)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <span className={`inline-flex rounded-full border px-3 py-1.5 text-[0.7rem] font-semibold uppercase tracking-[0.18em] ${getAlertStatusClasses(row.alertStatus)}`}>
                    {getAlertStatusLabel(row.alertStatus)}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <ul className="space-y-2 text-sm text-muted">
                    {row.topDrivers.slice(0, 3).map((driver) => (
                      <li key={driver}>{driver}</li>
                    ))}
                  </ul>
                </td>
                <td className="px-4 py-4 text-sm uppercase tracking-[0.18em] text-muted">{row.forecastAsOf}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
