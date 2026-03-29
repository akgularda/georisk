# Evergreen Website Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden the entire website so the core operational surfaces can keep showing the latest available prediction for the next highest-risk country for years without relying on manual editorial upkeep or brittle local artifact reads.

**Architecture:** Replace the current repo-local artifact discovery path with a canonical published site snapshot bundle, then make the website a stale-aware reader of that bundle. Separate machine-backed operational surfaces from optional curated editorial content, add durable publication and refresh flow, and remove the current fixed-country assumptions from ranking, routing, and hero rendering.

**Tech Stack:** Python 3.11, existing forecasting/backtesting artifacts, JSON publication bundle, GitHub Actions for development verification only, durable object/static storage, Next.js App Router, TypeScript, React, Tailwind CSS, MDX.

---

### Task 1: Define The Canonical Website Snapshot Contract

**Files:**
- Create: `georisk/contracts/website_snapshot.schema.json`
- Create: `georisk/contracts/model_card.schema.json`
- Create: `georisk/artifacts/examples/website_snapshot_example.json`
- Create: `georisk/src/website_publishing/schemas.py`
- Create: `georisk/src/tests/website_publishing/test_schemas.py`
- Modify: `georisk/docs/current_state.md`

**Step 1: Write the failing test**

Add schema tests that require:

- one canonical `manifest` / snapshot entrypoint
- per-country forecast entries with `iso3`, `country_name`, `score`, `delta`, `forecast_as_of`, `freshness_tier`
- provenance fields for training, calibration, and backtest runs
- explicit `baseline_used`, `stale_after`, and `published_at`
- model-card metrics and threshold policy fields

Run: `python -m pytest src/tests/website_publishing/test_schemas.py -q`

Expected: FAIL because no website publication schemas exist yet.

**Step 2: Create the schema contracts**

Implement:

- JSON schema for the website snapshot bundle
- JSON schema for the live model card payload
- Python schema/dataclass layer mirroring those contracts

**Step 3: Add an example artifact**

Write one checked-in example JSON bundle under `artifacts/examples/` so both Python and web code have a stable contract fixture.

**Step 4: Re-run the schema tests**

Run: `python -m pytest src/tests/website_publishing/test_schemas.py -q`

Expected: PASS

### Task 2: Build A Website Snapshot Publisher From Real Artifacts

**Files:**
- Create: `georisk/src/website_publishing/builder.py`
- Create: `georisk/src/website_publishing/cli.py`
- Create: `georisk/src/website_publishing/__init__.py`
- Create: `georisk/src/tests/website_publishing/test_builder.py`
- Create: `georisk/configs/website_publishing/site_snapshot.yaml`
- Modify: `georisk/docs/forecasting.md`
- Modify: `georisk/docs/backtesting.md`

**Step 1: Write the failing test**

Add builder tests that require the publisher to read:

- latest prediction artifacts
- latest backtest summary artifacts
- gold report inputs when available

and emit:

- `manifest.json`
- `forecast_snapshot.json`
- `countries/<iso3>.json`
- `backtest_summary.json`
- `model_card.json`
- `status.json`

Run: `python -m pytest src/tests/website_publishing/test_builder.py -q`

Expected: FAIL because no website snapshot builder exists yet.

**Step 2: Implement the minimal builder**

Builder rules:

- prefer calibrated live forecast outputs
- include top-country ordering in the bundle
- include current backtest comparison and live freshness metadata
- emit web-safe JSON only
- do not require the web app to parse Parquet or call `python`

**Step 3: Add baseline fallback publishing**

If the preferred model output is missing or invalid:

- publish from the safe baseline if available
- mark `baseline_used: true`
- never emit an apparently fresh live snapshot without provenance

**Step 4: Add a publisher CLI**

Run: `python -m src.website_publishing.cli --config configs/website_publishing/site_snapshot.yaml`

Expected: PASS and write a canonical website bundle to a local output directory.

**Step 5: Re-run the publisher tests**

Run: `python -m pytest src/tests/website_publishing/test_builder.py -q`

Expected: PASS

### Task 3: Add Durable Publication And Freshness Policy

**Files:**
- Create: `georisk/src/website_publishing/storage.py`
- Create: `georisk/src/tests/website_publishing/test_storage.py`
- Create: `georisk/docs/website_operations.md`
- Create: `georisk/.github/workflows/site-snapshot-verify.yml`
- Modify: `georisk/.github/workflows/web-publishing.yml`
- Modify: `georisk/configs/website_publishing/site_snapshot.yaml`

**Step 1: Write the failing test**

Add storage tests for:

- atomic latest-bundle publication
- immutable timestamped bundle directories
- a `latest` manifest pointer
- freshness-tier derivation from `published_at` and `forecast_as_of`

Run: `python -m pytest src/tests/website_publishing/test_storage.py -q`

Expected: FAIL because durable publication/storage logic does not exist yet.

**Step 2: Implement storage adapters**

Implement:

- local filesystem adapter for development
- provider-neutral durable storage interface for production publication

Publication rules:

- never rely on transient GitHub Actions artifacts as the only durable store
- keep immutable versioned bundles plus one canonical latest pointer

**Step 3: Document the production operating rule**

In `docs/website_operations.md`, document that:

- GitHub scheduled workflows are not the long-term production scheduler
- GitHub scheduled workflows in public repos can be disabled after 60 days without repo activity
- GitHub artifacts are not a durable publication store
- production needs an external scheduler or persistent platform-native scheduler

**Step 4: Wire verification workflow**

Add a workflow that verifies the snapshot contract and web consumption path on pushes, but does not pretend to be the only long-term production publisher.

**Step 5: Re-run tests**

Run: `python -m pytest src/tests/website_publishing -q`

Expected: PASS

### Task 4: Replace Repo-Local Artifact Loading With A Live Snapshot Loader

**Files:**
- Create: `georisk/web/src/lib/live-snapshot.ts`
- Create: `georisk/web/src/lib/freshness.ts`
- Create: `georisk/web/src/lib/status.ts`
- Modify: `georisk/web/src/lib/artifacts.ts`
- Modify: `georisk/web/src/lib/site-data.ts`
- Modify: `georisk/web/src/lib/types.ts`
- Create: `georisk/web/src/lib/__tests__/live-snapshot.test.ts`
- Modify: `georisk/web/package.json`

**Step 1: Write the failing test**

Add loader tests that require:

- loading the canonical JSON bundle without Parquet access
- explicit `fresh`, `aging`, `stale`, `critical`, and `missing` states
- deterministic fallback rules when the preferred snapshot is unavailable

Run: `npm run test -- live-snapshot`

Expected: FAIL because the web app still depends on local artifact path discovery and `python` subprocess execution.

**Step 2: Implement the live snapshot loader**

Implement:

- runtime fetch from one canonical snapshot URL or local fixture
- freshness-tier calculation
- status object returned alongside forecast data

Important:

- remove `python` subprocess dependency from the web runtime
- keep `artifacts.ts` only as a transitional compatibility layer or remove it fully

**Step 3: Add stale handling rules**

Rules:

- `fresh`: normal live rendering
- `aging`: warning copy
- `stale`: keep last published ranking but add visible stale-state banner
- `critical`: keep last published ranking and switch to hard warning state
- `missing`: explicit outage state, no silent curated operational ranking

**Step 4: Re-run tests**

Run: `npm run test -- live-snapshot`

Expected: PASS

### Task 5: Make Operational Pages Snapshot-Driven And Revalidating

**Files:**
- Modify: `georisk/web/src/app/page.tsx`
- Modify: `georisk/web/src/app/forecasts/page.tsx`
- Modify: `georisk/web/src/app/countries/page.tsx`
- Modify: `georisk/web/src/app/countries/[slug]/page.tsx`
- Create: `georisk/web/src/app/status/page.tsx`
- Create: `georisk/web/src/components/freshness-banner.tsx`
- Create: `georisk/web/src/components/system-status-panel.tsx`
- Modify: `georisk/web/src/components/monitor-table.tsx`
- Modify: `georisk/web/src/components/forecast-explorer.tsx`

**Step 1: Write the failing page contract**

The page contract should require:

- homepage lead from the canonical snapshot top country
- forecast board rows from the canonical snapshot only
- monitor ordering from the canonical snapshot only
- global stale-state banner when freshness degrades
- dedicated `/status` page with freshness, provenance, and fallback status

**Step 2: Add explicit revalidation policy**

Implement:

- route-level `revalidate` on operational pages
- optional on-demand revalidation hook for snapshot publish events
- no dependence on static generation of the current hand-curated country set

**Step 3: Remove silent operational fallback to curated ranking**

If the snapshot is missing:

- show explicit outage state
- keep editorial content visible where useful
- do not pretend the curated country order is live model output

**Step 4: Verify**

Run: `npm run lint`

Expected: PASS

Run: `npm run build`

Expected: PASS

### Task 6: Remove The Fixed-Country Constraint From Routing And Hero Rendering

**Files:**
- Modify: `georisk/web/src/data/countries.ts`
- Modify: `georisk/web/src/lib/types.ts`
- Modify: `georisk/web/src/components/country-pulse-graphic.tsx`
- Create: `georisk/web/src/lib/country-shape-registry.ts`
- Create: `georisk/web/src/lib/country-enrichment.ts`
- Modify: `georisk/web/src/app/countries/[slug]/page.tsx`
- Modify: `georisk/web/src/app/page.tsx`
- Modify: `georisk/web/scripts/validate-country-shapes.mjs`

**Step 1: Write the failing test**

Add validation that requires:

- the top country can render even if it is not one of the current hand-curated eight
- country pages can resolve from snapshot data alone
- shape rendering degrades gracefully when no exact shape exists

Run: `npm run shapes:validate`

Expected: FAIL because the site still assumes a narrow fixed `CountryShapeKey` universe.

**Step 2: Generalize country identity**

Implement:

- operational country identity by ISO3 / slug from snapshot data
- optional curated enrichment overlays when a country dossier exists
- no requirement that a country be pre-authored in `src/data/countries.ts` to appear on the site

**Step 3: Generalize hero rendering**

Preferred:

- exact shape for all forecastable countries if the shape registry can be expanded

Required:

- if a shape is missing, render a strong emergency plate with country name / ISO3 and no broken UI

**Step 4: Re-run validation**

Run: `npm run shapes:validate`

Expected: PASS

### Task 7: Convert Methodology Into A Live Trust Surface

**Files:**
- Modify: `georisk/web/content/methodology/data.mdx`
- Modify: `georisk/web/content/methodology/model.mdx`
- Modify: `georisk/web/content/methodology/backtesting.mdx`
- Create: `georisk/web/src/components/model-card-panel.tsx`
- Create: `georisk/web/src/components/source-freshness-table.tsx`
- Modify: `georisk/web/src/app/methodology/page.tsx`
- Modify: `georisk/web/src/app/methodology/[slug]/page.tsx`
- Modify: `georisk/web/src/lib/content.ts`
- Modify: `georisk/web/scripts/validate-content.mjs`

**Step 1: Write the failing content contract**

Require the methodology surface to expose:

- live model card summary
- current backtest summary
- source lag / freshness table
- explicit fallback and stale-state explanation

Run: `npm run content:validate`

Expected: FAIL because the methodology layer is still mostly static prose and one page is known to be outdated.

**Step 2: Implement live trust components**

Keep MDX for explanation, but add machine-backed panels for:

- current metrics
- freshness
- source revision / lag policy
- operational status

**Step 3: Align wording with reality**

Remove stale or misleading claims, especially around backtesting maturity and live coverage.

**Step 4: Re-run validation**

Run: `npm run content:validate`

Expected: PASS

### Task 8: Add Runtime Health, Revalidation Hook, And Smoke Coverage

**Files:**
- Create: `georisk/web/src/app/api/revalidate/route.ts`
- Create: `georisk/web/src/app/api/health/route.ts`
- Create: `georisk/web/scripts/validate-live-site.mjs`
- Create: `georisk/web/scripts/check-snapshot-freshness.mjs`
- Modify: `georisk/.github/workflows/web-publishing.yml`
- Modify: `georisk/docs/website_operations.md`

**Step 1: Write the failing smoke checks**

Checks must cover:

- fresh snapshot render
- stale snapshot render
- missing snapshot render
- artifact-only country route render
- `/status` and `/api/health` correctness

Run: `node web/scripts/validate-live-site.mjs`

Expected: FAIL because no runtime health endpoint or live smoke harness exists yet.

**Step 2: Add runtime status endpoints**

Implement:

- `/api/health` returning freshness tier, latest publish timestamp, and fallback status
- `/api/revalidate` for trusted on-demand revalidation after a new bundle publish

**Step 3: Add smoke validation scripts**

Implement scripts that fail if:

- the lead country is missing
- freshness metadata is absent
- snapshot age is beyond tolerated thresholds without warning copy

**Step 4: Wire workflow checks**

Add web checks that simulate:

- live bundle available
- stale bundle available
- no bundle available

**Step 5: Re-run checks**

Run: `node web/scripts/check-snapshot-freshness.mjs`

Expected: PASS

Run: `node web/scripts/validate-live-site.mjs`

Expected: PASS

### Task 10: Rebuild The Operational Design System As An Institutional Emergency Surface

**Files:**
- Modify: `georisk/web/src/app/globals.css`
- Modify: `georisk/web/src/app/layout.tsx`
- Modify: `georisk/web/src/app/page.tsx`
- Modify: `georisk/web/src/app/forecasts/page.tsx`
- Modify: `georisk/web/src/app/countries/page.tsx`
- Modify: `georisk/web/src/app/countries/[slug]/page.tsx`
- Modify: `georisk/web/src/app/status/page.tsx`
- Modify: `georisk/web/src/app/methodology/page.tsx`
- Modify: `georisk/web/src/components/country-pulse-graphic.tsx`
- Modify: `georisk/web/src/components/monitor-table.tsx`
- Modify: `georisk/web/src/components/forecast-explorer.tsx`
- Create: `georisk/web/src/components/operational-alert-strip.tsx`
- Create: `georisk/web/src/components/site-identity-strip.tsx`
- Create: `georisk/web/src/components/key-facts-strip.tsx`
- Create: `georisk/web/src/components/provenance-list.tsx`
- Create: `georisk/web/src/components/brief-kicker.tsx`
- Create: `georisk/docs/plans/2026-03-28-emergency-surface-design-research.md`
- Create: `georisk/docs/plans/2026-03-28-government-emergency-design-brief.md`

**Design Basis:**
- Use [2026-03-28-emergency-surface-design-research.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-28-emergency-surface-design-research.md) as the governing visual and usability brief.
- Use [2026-03-28-government-emergency-design-brief.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-28-government-emergency-design-brief.md) as the concrete implementation doctrine.

**Step 1: Define the visual contract**

The operational surfaces must satisfy these rules:

- one dominant lead country above the fold
- one top-level status strip only
- one institutional identity strip in the global shell
- no stacked warning banners
- red reserved for genuinely elevated states
- timestamps and provenance visible near major claims
- freshness, forecast-as-of, published time, and fallback visible in the first screenful
- tables and filters remain usable on mobile
- no decorative chrome that does not convey information
- sentence case for functional headings
- copy that reads like a government service rather than fictional command software

Expected current outcome: FAIL by inspection, because the current site still relies on terminal chrome, split-focus hero composition, and decorative alert styling.

**Step 2: Replace the current shell and typography**

Implement:

- a flatter graphite emergency shell
- stronger public-sector style heading rhythm
- a new operational font stack that avoids `Inter`
- restrained rules, panels, and spacing
- a disciplined emergency palette based on one hard red plus neutral surfaces

Required:

- no gradient-heavy panel stacking
- no repeated terminal micro-labels
- no background theatrics carrying the urgency
- no glow, scanline, reticle, or radar styling on operational surfaces

**Step 3: Rebuild the homepage and live operational pages**

Implement:

- one lead country assessment
- short fact-led briefing copy
- explicit freshness, fallback, forecast-as-of, and last-update rows
- calmer supporting rails for status and provenance
- one sitewide operational banner above page content
- one key-facts strip directly under the lead assessment

Apply the same direction to:

- `/`
- `/forecasts`
- `/countries`
- `/countries/[slug]`
- `/status`
- `/methodology`

**Step 4: Simplify operational components**

For tables, badges, and graphics:

- replace excess chips with direct labels
- keep status semantics explicit
- flatten country silhouette treatment
- remove decorative overlays
- preserve exact shapes where available, but make them locator artifacts instead of spectacle
- default comparison surfaces to table-first scanning rather than dashboard-card scanning
- keep critical meaning out of tiny badges alone

**Step 5: Verify usability and emergency-readability**

Run:

- `npm run lint`
- `npm run build`

Then browser-check:

- `/`
- `/forecasts`
- `/countries`
- `/countries/<artifact-only-country>`
- `/status`
- `/methodology`

Expected:

- the lead country is obvious within a five-second scan
- stale or fallback state is visible without hunting
- the pages feel like official emergency briefings, not like AI dashboard templates
- mobile interaction targets and hierarchy remain usable
- the site no longer reads as a generic AI product, startup dashboard, or cinematic command center

### Task 11: Final Verification And Handoff

**Files:**
- Modify only if verification reveals gaps

**Step 1: Run Python verification**

Run: `python -m pytest src/tests/website_publishing -q`

Expected: PASS

**Step 2: Run web verification**

Run: `npm run content:validate`

Expected: PASS

Run: `npm run lint`

Expected: PASS

Run: `npm run build`

Expected: PASS

**Step 3: Run live smoke verification**

Run: `node web/scripts/check-snapshot-freshness.mjs`

Expected: PASS

Run: `node web/scripts/validate-live-site.mjs`

Expected: PASS

**Step 4: Browser verify critical routes**

Inspect:

- `/`
- `/forecasts`
- `/countries`
- `/countries/<artifact-only-country>`
- `/status`
- `/methodology`

Expected:

- lead country matches canonical snapshot
- stale/missing states are explicit
- non-curated countries still render
- no operational ranking depends on static dossier order
- methodology page reflects current live trust state
