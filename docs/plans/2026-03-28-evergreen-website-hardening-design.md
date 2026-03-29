# Evergreen Website Hardening Approved Design

## Goal

Turn the current artifact-backed website into an evergreen publication surface that can keep showing the latest available prediction for the next highest-risk country even if no editor touches the site for years.

The requirement is not magical uptime. If upstream data or models fail, the site cannot invent truth. The real requirement is:

- keep a durable latest prediction surface alive
- make freshness and degradation explicit
- never silently fall back to hand-curated fiction for operational ranking
- ensure the visual and routing layer can handle whichever country rises next

## Current Failure Modes

The current site is good enough for an actively maintained demo, but not yet for unattended operation.

Main weaknesses from the repo:

- `web/src/lib/artifacts.ts` hardcodes local artifact paths, shells out to `python`, and memoizes the first successful read with no freshness invalidation
- `web/src/lib/site-data.ts` silently merges live overlays into a fixed curated dossier set and still uses that curated set as the operational backbone
- `web/src/app/countries/[slug]/page.tsx` uses `generateStaticParams()`, which is fine for a fixed editorial set but wrong for a forecast surface whose covered countries can change
- `web/src/data/countries.ts` and `web/src/lib/types.ts` still encode a narrow fixed country universe
- the hero and shape system are still biased toward the currently supported `shapeKey` set instead of the full forecastable country set
- `.github/workflows/web-publishing.yml` uses GitHub schedule, but GitHub documents that scheduled workflows in public repos are automatically disabled after 60 days without repository activity
- GitHub also documents that workflow artifacts/logs are retained for a limited period by default, so ephemeral workflow artifacts are not a durable publication store

## Recommendation

Use a canonical published site snapshot plus runtime refresh.

Recommended approach:

1. Build one canonical, web-safe snapshot bundle from forecasting and backtesting outputs.
2. Publish that bundle to durable storage that does not depend on ephemeral workflow artifacts.
3. Make the website read only that bundle for operational surfaces.
4. Add explicit freshness tiers, stale-state UX, and baseline fallback publishing.
5. Decouple country pages and visuals from the current hand-curated eight-country set.

This is stronger than either:

- hardening the current local artifact loader only
- committing regenerated JSON into the repo and rebuilding the site on a schedule

Why this is the right design:

- the website should consume JSON, not Parquet plus an ad hoc `python` subprocess
- the lead country should be determined by a published contract, not by whatever local file happened to exist at build time
- unattended operation requires a durable publisher plus a stale-aware reader, not only a nicer frontend

## Source Notes

External operating constraints worth designing around:

- GitHub documents that scheduled workflows in public repositories are automatically disabled after 60 days without repository activity:
  - https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
  - https://docs.github.com/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows
- GitHub documents that artifacts and logs are retained for a limited period by default, so workflow artifacts are not a durable long-term publication layer:
  - https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts
  - https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
- Next.js documents that ISR and on-demand revalidation are the correct primitives for refreshing published content without full rebuilds:
  - https://nextjs.org/docs/app/building-your-application/data-fetching/incremental-static-regeneration
  - https://nextjs.org/docs/13/app/api-reference/functions/revalidatePath

## Operating Invariants

The hardened website should obey these rules:

1. Homepage lead, forecast board ordering, and monitor ordering must come only from the latest published site snapshot.
2. The published snapshot must contain freshness metadata, provenance, and fallback flags.
3. If the preferred model path fails, the publisher must still emit a baseline-backed snapshot instead of leaving the site with no operational lead.
4. The site must never silently replace stale or missing live output with curated risk ordering.
5. The site must continue to render a country page for any country present in the published snapshot, even if no editorial dossier exists.
6. The visual layer must not constrain operational coverage. Exact country shapes are preferred, but missing shape art must never block rendering the lead country.
7. Methodology and model-trust surfaces must expose live status, current metrics, and freshness rather than depending on manually updated prose.

## Architecture

The system should split into four clear layers.

### 1. Forecast And Evaluation Layer

This layer already exists:

- dense weekly features
- forecasting train/calibrate/predict/explain
- backtesting artifacts

It remains the source of truth for model outputs.

### 2. Publication Layer

Add a dedicated website publication bundle builder that reads forecasting and backtesting artifacts and writes a stable JSON bundle with a single canonical contract.

Recommended bundle:

- `manifest.json`
- `forecast_snapshot.json`
- `countries/<iso3>.json`
- `backtest_summary.json`
- `model_card.json`
- `status.json`

Each bundle should include:

- `published_at`
- `forecast_as_of`
- `fresh_until`
- `stale_after`
- `source_run_ids`
- `model_name`
- `model_version`
- `baseline_used`
- `coverage_count`
- `top_country_iso3`

### 3. Storage And Delivery Layer

Publish the bundle to durable storage.

Preferred:

- object storage or a static JSON endpoint with durable retention

Acceptable secondary option:

- a dedicated branch or release asset strategy

Not acceptable as the primary durable store:

- transient GitHub Actions artifacts
- repo-local files discovered only at build time

### 4. Website Runtime Layer

The Next.js app should fetch the canonical bundle at runtime with controlled caching and revalidation.

Operational pages:

- `/`
- `/forecasts`
- `/countries`
- `/countries/[slug]`
- `/methodology`
- `/status`

The website should become a thin reader over the published bundle, not a local artifact parser.

## Freshness Policy

The UX must distinguish freshness tiers.

Recommended tiers for a weekly system:

- `fresh`: snapshot age <= 10 days
- `aging`: snapshot age 11-21 days
- `stale`: snapshot age 22-60 days
- `critical`: snapshot age > 60 days

Behavior:

- `fresh`: normal live presentation
- `aging`: warning badge, but still operational
- `stale`: show the last published top country, downgrade trust language, display stale banner globally
- `critical`: show the last published top country plus a hard warning that the publication chain is degraded
- `missing`: show explicit outage state, not curated operational fiction

Important rule:

The site should still show the last published prediction if it exists. It should not pretend to have a fresh prediction when it does not.

## Baseline Fallback Publishing

To satisfy the "still show the next problematic country" requirement, the publication layer needs a fallback ranking path.

Publishing order:

1. preferred calibrated model output
2. last successful preferred snapshot if still within allowed stale window
3. current baseline snapshot from `prior_rate` or equivalent safe baseline
4. explicit outage state if no valid snapshot can be produced

This moves fallback responsibility into publishing, where it belongs, instead of hiding it inside frontend view logic.

## Country Coverage Strategy

The current site is still biased toward the curated eight-country set. That is not acceptable for evergreen operation.

The hardening design should:

- support any ISO3 country present in the published snapshot
- expand the country shape registry beyond the current fixed union
- make exact shape optional at render time
- preserve a strong text-first emergency plate when no exact shape asset exists

Preferred visual rule:

- exact country shape when available
- generic alert plate plus ISO3 and country name when not

Operational ranking must never be blocked by art coverage.

## Editorial Strategy

Split the site into two content classes.

### Operational Surfaces

These must be machine-backed and evergreen:

- homepage lead
- forecast board
- monitor table
- country ranking
- country current signals
- live methodology/status/model metrics

### Editorial Surfaces

These can remain curated and optional:

- long reports
- scenario notes
- historical timelines
- hand-authored country briefs

If editorial content goes stale, the operational surfaces should still work.

## Trust And Methodology Surfaces

The methodology section should stop being a static prose-only island.

It should include live machine-fed trust surfaces:

- current model card
- current backtest summary
- freshness and coverage table
- source lag and revision policy table
- fallback status

Static MDX pages should explain the system, not pretend to be the live status layer.

## Design Addendum: Institutional Emergency UX

The website also needs a visual hardening pass. Evergreen data architecture alone is not enough if the operational surfaces still read like generic AI-dashboard chrome.

The design direction should be:

- text-first
- institutional
- official
- severe
- urgent without being sensational

The design should move toward an **Institutional Emergency Operations** system:

- one dominant lead country above the fold
- one top-level operational status strip
- flatter panels and fewer decorative frames
- stronger typographic hierarchy with public-sector style discipline
- timestamps, provenance, and freshness shown close to the claim
- exact country shapes used as locator artifacts, not as decorative theater

The current website should explicitly move away from:

- repeated terminal chrome
- stacked panel emphasis
- too many chips and micro-labels
- gradient-led urgency
- split-focus hero structures
- atmospheric intelligence styling that looks synthetic rather than official

This is a usability requirement, not only a branding preference. On an emergency or monitoring surface, visual drama competes with comprehension.

The full research basis is documented in [2026-03-28-emergency-surface-design-research.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-28-emergency-surface-design-research.md).

The governing implementation brief is [2026-03-28-government-emergency-design-brief.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/docs/plans/2026-03-28-government-emergency-design-brief.md).

## Verification And Monitoring

The hardened system needs explicit checks:

- schema validation for every published bundle
- freshness validation in CI
- smoke tests for `fresh`, `stale`, and `missing` snapshot modes
- route tests for an artifact-only country with no curated dossier
- build test that succeeds without local Parquet access
- runtime status endpoint for uptime and freshness monitoring

## Acceptance Criteria

The design is successful when all of these are true:

- the homepage lead country is derived from a canonical published snapshot, not from curated fallback ranking
- the site can render a lead country that is not in the current hand-curated dossier set
- stale and missing states are explicit and honest
- the website no longer depends on `python` subprocess execution or repo-local Parquet parsing at runtime
- the publication chain has a durable store that survives beyond GitHub artifact retention
- unattended operation does not rely solely on GitHub scheduled workflows
- methodology and trust pages expose live metrics and freshness instead of manually maintained claims
- operational pages feel like official emergency briefings rather than AI-generated dashboards
- visual urgency comes from hierarchy, evidence, and status semantics rather than decorative effects
- mobile and accessibility scanning remain strong under stress conditions
