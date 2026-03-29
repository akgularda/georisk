import { type ConfidenceBand, type OperationalAlertStatus, type RiskCategory } from "@/lib/types";

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

export function formatDateTime(date: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(date));
}

export function formatDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${delta} pts`;
}

export function formatProbabilityPercent(probability: number): string {
  return `${(probability * 100).toFixed(probability >= 0.01 ? 1 : 2)}%`;
}

export function formatProbabilityBps(probability: number): string {
  return `${Math.round(probability * 10000)} bps`;
}

export function formatProbabilityDelta(delta: number): string {
  const sign = delta > 0 ? "+" : "";
  return `${sign}${(delta * 100).toFixed(Math.abs(delta) >= 0.01 ? 1 : 2)} pp`;
}

export function getRiskToneClasses(category: RiskCategory): string {
  switch (category) {
    case "Critical":
      return "border-[#d9574f]/40 bg-[#261111] text-[#ff827a]";
    case "High":
      return "border-[#d9574f]/24 bg-[#1e1518] text-[#f3a39e]";
    case "Elevated":
      return "border-[#cfa14a]/28 bg-[#221b12] text-[#dfbf73]";
    default:
      return "border-border bg-surface-muted text-muted";
  }
}

export function getConfidenceLabelClasses(confidenceBand: ConfidenceBand): string {
  switch (confidenceBand) {
    case "High":
      return "border border-[#48c06a]/28 bg-[#102319] text-[#7edc97]";
    case "Moderate":
      return "border border-[#cfa14a]/28 bg-[#241d13] text-[#dfbf73]";
    default:
      return "border border-border bg-surface-muted text-muted";
  }
}

export function getAlertStatusClasses(status: OperationalAlertStatus): string {
  switch (status) {
    case "alert":
      return "border-[#f06758]/55 bg-[#351010] text-[#ffd0ca]";
    case "warning":
      return "border-[#f06758]/35 bg-[#261214] text-[#f5b0aa]";
    case "operating":
      return "border-[#d2a255]/35 bg-[#261d10] text-[#f1d28a]";
    default:
      return "border-[rgba(146,154,168,0.22)] bg-[rgba(12,16,22,0.92)] text-[#a4adb9]";
  }
}

export function getAlertStatusLabel(status: OperationalAlertStatus): string {
  switch (status) {
    case "alert":
      return "Alert threshold";
    case "warning":
      return "Warning threshold";
    case "operating":
      return "Operating threshold";
    default:
      return "Below threshold";
  }
}
