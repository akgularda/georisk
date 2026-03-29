import type { FreshnessTier } from "@/lib/types";

const DAY_IN_MS = 24 * 60 * 60 * 1000;

export const LIVE_SNAPSHOT_FRESH_WINDOW_DAYS = 10;
export const LIVE_SNAPSHOT_AGING_WINDOW_DAYS = 21;
export const LIVE_SNAPSHOT_CRITICAL_WINDOW_DAYS = 60;

function toAgeDays(publishedAt: string, now: Date): number | null {
  const publishedTime = Date.parse(publishedAt);
  if (Number.isNaN(publishedTime)) {
    return null;
  }
  return Math.floor((now.getTime() - publishedTime) / DAY_IN_MS);
}

export function getFreshnessTierForAge(ageDays: number | null | undefined): FreshnessTier {
  if (ageDays === null || ageDays === undefined || !Number.isFinite(ageDays)) {
    return "missing";
  }
  if (ageDays <= LIVE_SNAPSHOT_FRESH_WINDOW_DAYS) {
    return "fresh";
  }
  if (ageDays <= LIVE_SNAPSHOT_AGING_WINDOW_DAYS) {
    return "aging";
  }
  if (ageDays <= LIVE_SNAPSHOT_CRITICAL_WINDOW_DAYS) {
    return "stale";
  }
  return "critical";
}

export function getFreshnessTierFromPublishedAt(publishedAt: string | null | undefined, now = new Date()): FreshnessTier {
  if (!publishedAt) {
    return "missing";
  }
  return getFreshnessTierForAge(toAgeDays(publishedAt, now));
}

export function getFreshnessTierFromSnapshotBounds({
  publishedAt,
  freshUntil,
  staleAfter,
  now = new Date(),
}: {
  publishedAt?: string | null;
  freshUntil?: string | null;
  staleAfter?: string | null;
  now?: Date;
}): FreshnessTier {
  if (freshUntil) {
    const freshUntilTime = Date.parse(freshUntil);
    if (!Number.isNaN(freshUntilTime) && now.getTime() <= freshUntilTime) {
      return "fresh";
    }
  }

  if (staleAfter) {
    const staleAfterTime = Date.parse(staleAfter);
    if (!Number.isNaN(staleAfterTime) && now.getTime() <= staleAfterTime) {
      return "aging";
    }
  }

  return getFreshnessTierFromPublishedAt(publishedAt, now);
}
