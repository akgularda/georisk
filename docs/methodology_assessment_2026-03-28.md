# Methodology Assessment

Date: 2026-03-28

## Executive Summary

The methodology is directionally good, but not yet strong enough to present as a mature, externally convincing forecasting methodology.

What is good:

- the implemented system uses time-ordered splits instead of random reshuffling
- the pipeline separates training, calibration, prediction, explanation, and backtesting
- the feature stack is multi-source rather than single-feed
- the system explicitly separates risk score from confidence
- backtesting artifacts, alert metrics, and replay artifacts now exist

What is not yet good enough:

- the public methodology pages are too thin and in one case factually outdated
- the website does not document the actual target construction, model classes, feature lag rules, missing-data handling, or threshold policy
- the current empirical evidence is weak: the richer weekly model does not yet beat the baseline on PR AUC, and the current backtest produced zero alerts on one label episode
- point-in-time integrity is stated as a goal, but the public methodology does not spell out revision handling or source-specific publication lag rules in enough detail to verify the claim

Bottom line:

- as an internal methodology foundation, this is promising
- as a public-facing methodology for trust, it is not yet sufficient
- the next step is not cosmetic rewriting; it is to close the documentation-to-implementation gap and publish stronger empirical evidence

## Research Questions

1. Does the current georisk methodology align with good practice for conflict early warning and probabilistic forecasting?
2. Are the chosen source families and time-integrity claims methodologically credible?
3. Is the current validation and backtesting design strong enough for public trust?
4. What should change before the methodology is presented as robust?

## Local Evidence Reviewed

Public methodology pages:

- `web/content/methodology/data.mdx`
- `web/content/methodology/model.mdx`
- `web/content/methodology/backtesting.mdx`

Implementation and docs:

- `docs/forecasting.md`
- `docs/backtesting.md`
- `docs/current_state.md`
- `configs/forecasting/train_country_week_logit_30d.yaml`
- `configs/backtesting/country_week_logit.yaml`

Artifacts:

- `artifacts/forecasting/train/country_week_logit_30d/metrics.json`
- `artifacts/backtesting/run/country_week_logit/metrics.json`
- `artifacts/backtesting/run/country_week_logit/summary.md`

## External Benchmarks Reviewed

- ViEWS 2019: transparency, public availability, and uniform coverage as explicit design goals
  - https://academic.oup.com/jpr/article/56/2/155/8365298
- ViEWS 2020: separate training, calibration, and forecasting periods; AUPR and Brier used for evaluation
  - https://academic.oup.com/jpr/article/58/3/599/8365273
- UCDP Candidate Events / ViEWS Outcomes: monthly point-in-time conflict updates, explicitly distinguished from final vetted data
  - https://viewsforecasting.org/publications/introducing-the-ucdp-candidate-events-dataset-and-the-views-outcomes-dataset-monthly-updated-organized-violence-data-in-the-form-of-events-data-as-well-as-aggregated-to-the-country-month-and-prio-gri/
- ACLED Codebook: weekly publication, multi-stage review, living dataset, revisions to events and fatalities
  - https://acleddata.com/methodology/acled-codebook
- GDELT documentation: near-real-time updates every 15 minutes
  - https://blog.gdeltproject.org/announcing-our-first-api-gkg-geojson/
- UNHCR Refugee Data Finder methodology: mixed publication cadence and quality framework
  - https://www.unhcr.org/refugee-statistics/methodology
  - https://www.unhcr.org/refugee-statistics/insights/explainers/statistical-quality-assurance-framework.html
- World Bank WDI methodology: revisions over time and timing inconsistencies across sources
  - https://datahelpdesk.worldbank.org/knowledgebase/articles/114939-how-are-revisions-managed
  - https://datahelpdesk.worldbank.org/knowledgebase/articles/906531-methodologies
- scikit-learn official docs: time-series splitting and calibration guidance
  - https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
  - https://scikit-learn.org/stable/modules/calibration.html
  - https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html

## Findings

### 1. The overall methodological direction is sound

The repo is making several choices that are consistent with serious forecasting practice:

- walk-forward / time-ordered validation
- post-training calibration
- explicit baseline comparison
- artifact persistence and provenance checks
- separate treatment of risk score and confidence

That is materially better than the typical "single model, random split, no calibration" setup.

The strongest local evidence is:

- `configs/forecasting/train_country_week_logit_30d.yaml` uses time-based windows (`min_train_periods`, `validation_window_periods`, `step_periods`)
- `configs/backtesting/country_week_logit.yaml` mirrors that structure in backtesting
- `docs/forecasting.md` and `docs/backtesting.md` document saved calibration and backtest artifacts

This aligns with external standards:

- scikit-learn states that ordinary cross-validation is inappropriate for ordered data because it would train on future data and evaluate on past data
- ViEWS 2020 uses separate training, calibration, and testing/forecasting periods rather than blending them

### 2. The source stack is sensible, but the point-in-time methodology is under-specified

Using distinct source families is a good choice. The platform combines event, narrative, macro, governance, election, climate, trade, shipping, humanitarian, and security features.

That is consistent with conflict forecasting literature, where:

- fast-moving event streams capture current stress
- slower structural covariates help distinguish low- and high-risk cases over longer horizons

ViEWS 2020 explicitly notes that slow-moving structural features can become more useful at longer horizons.

However, the public methodology understates the actual complexity and does not document the key caveats strongly enough:

- `web/content/methodology/data.mdx` mentions GDELT, UCDP GED, UNHCR, and WDI, but the implemented weekly model also uses ACLED and many additional families
- GDELT is near-real-time, but World Bank and UNHCR indicators are slower and revised on different cycles
- ACLED is a living dataset and may revise events and fatalities later
- WDI states that historical data may change with each update and that differences in timing and reporting practices can cause inconsistencies

This means the current claim of point-in-time integrity is plausible as an aspiration, but not yet publicly auditable. The site needs source-by-source lag and revision rules, not just a sentence saying the goal exists.

### 3. The validation design is good in principle, but the public methodology is outdated

This is the largest credibility problem in the public methodology right now.

`web/content/methodology/backtesting.mdx` still says:

- the full backtesting package is not complete yet
- the page describes the intended validation shape

That is no longer accurate relative to:

- `docs/current_state.md`
- `docs/backtesting.md`
- `artifacts/backtesting/run/country_week_logit/*`

So the methodology section is currently failing one of the most important trust tests: it does not accurately describe the system that exists.

### 4. The current empirical evidence is not yet strong

This is the core methodological limitation.

From `artifacts/backtesting/run/country_week_logit/summary.md`:

- top-performing model: `prior_rate`
- `prior_rate` PR AUC: `0.0007407407407407407`
- `logit` PR AUC: `0.00044918585064570465`
- both models had `precision = 0`, `recall = 0`, `f1 = 0`
- new alerts: `0`
- true alerts: `0`
- false alerts: `0`
- label episodes: `1`

From `artifacts/forecasting/train/country_week_logit_30d/metrics.json`:

- `logit` PR AUC is below the baseline
- one fold had to be skipped because the training slice had zero positive cases

Interpretation:

- the methodology structure is reasonable
- the current weekly data regime is still too sparse or too imbalanced to support strong public claims about predictive performance
- ROC AUC is not enough here; PR AUC is more relevant because the class is very imbalanced, and the current PR performance is weak

This matches external guidance:

- scikit-learn notes that precision-recall is especially useful when classes are very imbalanced
- ViEWS 2020 emphasizes AUPR and Brier, not just ROC AUC

### 5. The public methodology is not reproducible enough

A credible public methodology should tell a technically serious reader:

- what the target event is
- how labels are generated
- what counts as a positive
- what the forecast issue date and target window are
- how missing values are handled
- how thresholds are chosen
- how scores are calibrated
- what baselines are used
- how often the model is retrained
- how revisions in historical data are handled
- what the current measured performance is

The current website methodology pages do not yet do that.

They are good caveat copy, but not yet a real methodology.

## Analysis

### Is the methodology good?

Yes in architecture.

No in current public evidence.

More precisely:

- the implemented architecture is good enough to continue investing in
- the current public methodology is not good enough to earn strong external trust
- the current empirical results are not yet good enough to claim the model is operationally effective

This is a normal stage for an early system, but it should be described honestly.

### What is strongest right now

- time-aware validation
- calibration as a first-class step
- baseline comparisons
- multi-source feature design
- explicit caveats instead of false certainty

### What is weakest right now

- mismatch between public methodology pages and actual implementation state
- lack of source-specific point-in-time / revision policy
- no published threshold-selection logic
- no published model card or performance table
- weak current evidence on rare-event prediction quality

## Recommendations

### Priority 1: Fix the public methodology to match reality

Update the website methodology pages so they accurately reflect the implemented system:

- backtesting is implemented, not merely planned
- weekly country-week forecasting is implemented
- the active model families and baselines are named
- the current limitations are empirical, not only architectural

### Priority 2: Publish a real model card

Create a public model card that includes:

- target definitions
- unit of analysis
- forecast horizons
- positive class prevalence
- train/calibration/test window policy
- baselines
- calibration method
- threshold policy
- current metrics by target and horizon
- known failure modes

The existing `docs/model_card_template.md` is a strong place to start.

### Priority 3: Make point-in-time claims auditable

Document source-specific release and revision policy:

- GDELT: near-real-time feed behavior
- ACLED: weekly releases and later revisions
- UCDP GED vs UCDP Candidate handling
- UNHCR semiannual and annual cadence
- WDI revision behavior and annual lag

If possible, publish a simple table with:

- source
- event date
- publication/update cadence
- revision risk
- lag applied before modeling
- snapshot versioning rule

### Priority 4: Strengthen the rare-event evaluation story

Before treating the methodology as mature, publish:

- PR AUC versus prevalence baseline
- calibration plots
- alert burden / lead time metrics
- threshold sensitivity analysis
- per-target and per-horizon performance, not just one weekly setup

Right now the empirical story is too weak to support a strong trust claim.

### Priority 5: Separate "good warning architecture" from "proven predictive performance"

The system can honestly claim:

- disciplined warning architecture
- transparent caveats
- time-aware evaluation design

It should not yet strongly claim:

- robust predictive superiority over baseline
- operational alert effectiveness
- mature calibration under sparse positive labels

## Recommended Public Positioning

The honest public claim is:

> This is a disciplined, artifact-backed early-warning system with time-aware validation and explicit uncertainty, but the public methodology and empirical validation are still maturing.

That claim is defensible.

The stronger claim:

> This is already a proven forecasting methodology

is not yet defensible from the current artifacts.

## Source Notes

Most important source comparisons:

- ViEWS is the clearest benchmark for a transparent conflict early-warning methodology
- ACLED, UCDP, UNHCR, and WDI all explicitly document revision, cadence, or quality limitations that should be mirrored in this project's methodology
- scikit-learn official docs support the current use of time-ordered splits, calibration, and precision-recall emphasis for imbalanced prediction

## Final Judgment

The methodology is promising and structurally respectable, but not yet strong enough to present as fully mature.

If the goal is internal confidence: good enough to keep building.

If the goal is external credibility: not yet. The system needs better public documentation and stronger out-of-sample evidence first.
