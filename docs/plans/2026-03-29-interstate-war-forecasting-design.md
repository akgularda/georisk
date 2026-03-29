# Interstate War Forecasting Approved Design

## Goal

Extend GeoRisk from a generic organized-violence monitor into a forecasting system that can:

- forecast broad conflict onset before it is obvious
- forecast interstate war onset as a separate first-class problem
- prove its claims with explicit held-out evidence
- avoid false precision when the signal is flat

The Iran check established the current gap clearly: the website can publish a hardened monitoring surface, but the target stack is not yet built to capture interstate war onset.

## Problem Statement

The current backend is onset-first for generic organized violence, but interstate war is not operationally modeled.

Current repo findings:

- [country_week_features.py](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/src/data_platform/serving/country_week_features.py) hard-codes `label_interstate_30d` to `pd.NA`
- [entity_day_labels.py](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/src/data_platform/serving/entity_day_labels.py) does not export any interstate labels
- the operational configs in [train_country_week_onset_logit_30d.yaml](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/configs/forecasting/train_country_week_onset_logit_30d.yaml) and [train_country_week_onset_structural_90d.yaml](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/configs/forecasting/train_country_week_onset_structural_90d.yaml) only train generic onset models
- the live Iran/Israel replay before February 28, 2026 showed no usable interstate warning signal

This is a target-definition failure first, not merely a model-tuning failure.

## Approaches Considered

### Approach 1: Derive interstate war labels directly from GED heuristics

Use UCDP GED `type_of_violence == 1`, actor names, and conflict strings to guess interstate starts.

Why not:

- GED is event-level and rich, but it is not itself the authoritative onset definition
- pure heuristics will drift and create avoidable label noise
- this would make methodology harder to defend

### Approach 2: Use official UCDP onset datasets for truth and GED for onset dates

Use the official UCDP interstate and intrastate country-level onset datasets as the annual truth table, then join those official onset years to GED conflict ids to recover the first event date inside the onset year.

Why this is the recommended path:

- official UCDP onset datasets provide the defensible definition of interstate and intrastate onset
- GED provides the date resolution needed for weekly 30d and 90d forecasting
- this keeps labels methodologically grounded while preserving near-term operational horizons

### Approach 3: Skip weekly horizons and forecast only annual war onset

Use the UCDP onset datasets directly and move the product to annual risk forecasts.

Why not:

- it weakens the operational value of the site
- it does not align with the current weekly feature and publishing architecture
- the website is already built around frequent refresh and short-horizon monitoring

## Recommendation

Adopt Approach 2.

That means:

1. ingest the official UCDP interstate and intrastate country-level onset datasets
2. normalize them into country-year truth tables
3. localize each official onset year to an onset date using GED conflict ids
4. rebuild weekly labels from those localized onset dates
5. train separate conflict-onset and interstate-war-onset models
6. publish both surfaces distinctly on the website

## Label Strategy

### Official Truth Layer

Use:

- UCDP Interstate Country Level Onset Dataset version 25.1
- UCDP Intrastate Country Level Onset Dataset version 25.1

These datasets provide annual country-level onset flags such as `newconf`, `onset1`, `onset2`, and `onset3`. For GeoRisk, the initial operational interpretation should use `onset1` as the shortest restart rule.

### Date Localization Layer

For each official onset country-year:

- parse the `conflict_ids` field from the onset dataset
- join those ids to GED `conflict_new_id`
- for the matching country-year, recover the earliest `event_date_start`

This produces a localized onset date that is still anchored to official UCDP onset truth.

### Weekly Operational Labels

From the localized onset dates, generate:

- `label_conflict_onset_30d`
- `label_conflict_onset_90d`
- `label_interstate_onset_30d`
- `label_interstate_onset_90d`

Also preserve:

- `label_escalation_7d`
- `label_escalation_30d`

Compatibility policy:

- keep `label_onset_30d` and `label_onset_90d`, but redefine them as aliases of `label_conflict_onset_30d` and `label_conflict_onset_90d`
- replace the old heuristic onset definition entirely once the official-onset path is green

## Feature Strategy

Conflict onset and interstate war onset should share the same core table but not the same exact feature emphasis.

### Shared trigger features

- ACLED recent activity and acceleration
- GDELT event and document acceleration
- quiet-window flags
- actor novelty
- market and shipping stress
- governance, macro, security, and humanitarian baselines

### Interstate-war specific emphasis

- state-based conflict history
- oil, gas, fertilizer, and shipping shocks
- strategic developments
- remote violence and explosion changes
- neighbor and regional spillover
- military expenditure and arms-import baselines

The current repo already has many of these columns. The first phase should reuse the existing table and add only narrowly justified interstate-specific features where needed.

## Model Stack

### 1. Broad conflict onset

- structural prior: 90d official conflict onset
- trigger model: 30d official conflict onset

### 2. Interstate war onset

- structural prior: 90d official interstate onset
- trigger model: 30d official interstate onset

### 3. Escalation

- keep as a secondary operational track

Operational semantics:

- homepage remains conflict-first
- status page and methodology expose both conflict onset and interstate war onset
- if interstate watch has a stronger signal than conflict onset, publish that separately rather than folding it into the same alert sentence

## Backtesting Policy

Required evidence for promotion:

- explicit held-out backtests for conflict onset and interstate onset
- recent replay analysis for the 2024 boundary and all available post-2015 onset episodes
- clear separation between baseline and candidate performance

Required metrics:

- PR AUC
- recall@5
- recall@10
- episode recall
- median lead days
- false alerts per true alert
- no-clear-leader rate

If the candidate model does not beat baseline on the operational metrics, publish `monitoring_only`.

## Website Semantics

Add a distinct public watch surface:

- `Conflict Onset Watch`
- `Interstate War Watch`
- `Escalation Watch`
- `Monitoring Only`
- `No Clear Leader`

The website should never imply that a war forecast exists unless the interstate model and its provenance are present in the published snapshot.

## Initial Acceptance Criteria

This phase is complete when all of the following are true:

- official UCDP onset datasets are ingested and normalized
- weekly labels include real `label_interstate_onset_30d` and `label_interstate_onset_90d`
- conflict onset labels use the official-onset-plus-GED path instead of the old heuristic
- interstate structural and trigger models train and predict successfully
- interstate backtests run successfully and publish summary artifacts
- website snapshot includes interstate provenance and interstate status fields
- homepage or status page surfaces the interstate watch honestly

## Recommendation Lock

Proceed with:

- official UCDP onset truth
- GED-based onset-date localization
- parallel conflict and interstate forecasting paths
- explicit website publishing of interstate watch status
