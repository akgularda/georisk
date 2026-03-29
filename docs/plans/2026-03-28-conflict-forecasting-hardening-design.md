# Conflict Forecasting Hardening Approved Design

## Goal

Shift GeoRisk from a generic weekly country-risk ranking into a real early-warning system whose primary job is:

- surface the next country most likely to enter organized violence before that conflict is obvious
- separate onset risk from escalation risk instead of collapsing them into one score
- publish only alerts that are defensible under backtesting
- show "no clear leader" when the system does not have a sharp signal

The requirement is not to look dramatic. The requirement is to improve lead time while keeping false-alert burden low enough that the surface remains credible.

## Current Problems

The current system is operationally coherent, but it is not yet optimized for "predict conflict before it happens."

Main weaknesses from the repo and live artifacts:

- the active website lead is still driven by a single weekly `logit` escalation path rather than an onset-first warning stack
- the current preferred model does not beat the baseline on PR AUC in [summary.md](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/artifacts/backtesting/run/country_week_logit/summary.md)
- the latest backtest produced zero alerts, which means the system is not yet demonstrating actionable warning behavior
- the training config in [train_country_week_logit_30d.yaml](/C:/Users/akgul/Downloads/codex_prompts_georisk/georisk/configs/forecasting/train_country_week_logit_30d.yaml) still uses a fixed `prediction_threshold: 0.5`, which is rarely the right operating rule for a rare-event monitor
- the site currently forces a lead country even when the live snapshot has a broad tie set
- slow structural features and fast trigger features are mixed into one short-horizon classifier without a clear operational separation

## Approaches Considered

### Approach 1: Keep the single weekly classifier and tune it harder

This is the lowest-effort path:

- keep one weekly model
- add more features
- tune thresholds

Why it is not enough:

- it still mixes onset and escalation logic
- it does not make the homepage tell the user what kind of risk is being shown
- it is unlikely to fix the core trust problem if the model still cannot produce useful alerts

### Approach 2: Onset-first warning stack with escalation fallback

This is the recommended approach:

- make conflict onset the primary operational target
- keep escalation as a secondary target for already-active countries
- add trigger-oriented features and explicit threshold selection from backtests
- add a "no clear leader" state when the ranking is weak

Why this is the right design:

- it matches the actual product goal: predict conflict before it happens
- it is implementable on the current repo without a full research rewrite
- it makes the website semantics much clearer

### Approach 3: Event-level hazard or sequence model

This is the long-term research path:

- move from country-week classifiers to survival or sequence models
- treat onset as a hazard process rather than a simple thresholded classification task

Why this is not the immediate recommendation:

- it is methodologically attractive, but it is a phase-two or phase-three move
- the current repo should first prove value with a cleaner country-week onset stack and better operating metrics

## Recommendation

Adopt Approach 2 now.

That means:

1. make onset risk the primary operational surface
2. keep escalation as a secondary operational surface
3. add stronger trigger features and explicit publication gates
4. publish abstention honestly when the ranking is weak

## Operating Objective

The platform should optimize for this outcome:

> Detect the next country likely to cross from a quiet or low-violence state into meaningful organized violence within 30 days, while keeping false alerts low enough that analysts would still trust the feed.

That objective implies:

- onset is primary
- escalation is secondary
- persistence is context, not the homepage lead
- the model should be judged on episode capture and lead time, not only raw probability calibration

## Target Stack

The operational stack should separate targets rather than forcing one score to do all jobs.

### 1. Primary: Organized Violence Onset 30d

Use `label_onset_30d` as the initial operational anchor, then harden its definition if needed.

Recommended semantics:

- country is quiet or near-quiet over the recent lookback window
- meaningful organized violence appears in the next 30 days
- the site labels this as `Onset Watch`

This is the direct answer to "before it happens."

### 2. Secondary: Organized Violence Escalation 30d

Use `label_escalation_30d` as the secondary operational track.

Recommended semantics:

- country already has some conflict activity
- the next 30 days imply a material worsening or spread
- the site labels this as `Escalation Watch`

This matters for active theaters, but it should not crowd out onset detection.

### 3. Context Only: Interstate / Persistence / Humanitarian Stress

These should remain supporting surfaces unless they prove strong enough to become first-class alerts.

Use them as:

- explanation context
- risk amplifiers
- scenario notes

Do not let them replace the onset lead.

## Feature Strategy

The current feature family coverage is directionally good, but the operational mix needs to change.

### Keep

- ACLED and GDELT event intensity
- tone and attention measures
- elections, governance, macro, climate, trade, shipping, humanitarian, and long conflict history

### Add

- short-vs-medium acceleration features: 7d vs 28d, 14d vs 56d
- first-difference and z-score features for fatalities, protests, riots, and remote violence
- novelty features: first recent appearance of armed activity, new actor counts, first recent border incident
- border contagion features using neighbor and regional spillover exposure
- sharper quiet-period flags for onset logic
- rank and percentile features within the global panel so the model knows whether a country is unusual this week

### Reframe

Slow structural variables should become context or priors, not the main source of short-horizon trigger behavior.

The weekly trigger model should be dominated by:

- recent changes
- recent novelty
- recent spillover
- recent attention acceleration

## Model Architecture

### Phase 1: Dual operational models

Train and publish:

- a primary onset model for `label_onset_30d`
- a secondary escalation model for `label_escalation_30d`

Both should have:

- explicit `prior_rate` baseline
- `logit` as the first richer benchmark
- optional LightGBM or ensemble challenger only if it materially beats baseline on rare-event metrics

### Phase 2: Structural prior plus trigger layer

Once onset metrics are stable, add a two-layer stack:

1. a slower structural onset prior using slow variables and long history
2. a fast weekly trigger model using recent dynamics plus the prior score as an input

This is the preferred future architecture, but not required for the first operational hardening pass.

## Threshold And Publication Policy

The site should stop using a generic `0.5` operating threshold.

Replace it with backtest-selected thresholds and explicit abstention rules.

### Required threshold policy

For each operational target, publish:

- `publish_threshold`
- `warning_threshold`
- `alert_threshold`
- `separation_margin`

Select them from walk-forward backtests using:

- episode recall
- recall at top-k
- median lead days
- false alerts per true alert
- overall alert burden

### Required abstention rule

The homepage must show `No Clear Leader` when any of these are true:

- no country exceeds the publish threshold
- the top score is too close to the next score
- the top rank is part of a large tie set
- the candidate model failed promotion gates and only a monitoring-grade output is available

This is a methodological requirement, not a UX preference.

## Promotion Gates

No model should drive the homepage just because it exists.

Promote a candidate model only if it beats the explicit baseline on the relevant operating metrics.

Required gates for a promoted onset model:

- PR AUC >= baseline
- recall@10 > baseline
- episode recall > baseline
- median lead days > 0
- false alerts per true alert within an agreed ceiling

If the candidate fails those gates:

- keep it in research/challenger status
- publish the site in monitoring mode or use the better baseline-backed surface

## Website Semantics

The site should publish a richer machine-backed alert contract.

Required public fields:

- `primary_target`
- `alert_type`
- `model_status`
- `publish_threshold`
- `alert_threshold`
- `no_clear_leader`
- `episode_recall`
- `recall_at_5`
- `recall_at_10`
- `median_lead_days`
- `false_alerts_per_true_alert`
- `baseline_delta_pr_auc`

The homepage lead should explicitly say whether it is:

- `Onset Watch`
- `Escalation Watch`
- `Monitoring Only`
- `No Clear Leader`

## What To Add

- onset-first configs, backtests, and publication contract
- trigger-oriented change and novelty features
- top-k and episode-level evaluation
- threshold selection driven by alert burden
- abstention behavior
- live model card and empirical trust surface

## What To Remove

- fixed `0.5` as the operational threshold
- the assumption that one lead country must always be shown
- any public implication that the current preferred model is proven just because it is richer
- overreliance on slow annual features inside the short-horizon public alert score
- language on the methodology pages that still describes backtesting as unfinished

## Acceptance Criteria

The design is successful when all of these are true:

- the homepage lead is onset-first by policy, not escalation-first by accident
- the site can explicitly say `No Clear Leader` instead of inventing a sharp ranking
- the promoted model beats the explicit baseline on the chosen rare-event operating metrics
- the published bundle exposes lead-time and alert-burden metrics, not only generic probability fields
- methodology pages match the real system and current evidence
- the platform can honestly claim it is trying to predict conflict before it happens, not only rank generic instability
