# Model Card Template

## Model Overview

- Model name:
- Version:
- Primary target:
- Secondary target:
- Structural prior layer:
- Alert type surface:
- Horizon:
- Unit of analysis:
- Training window:
- Model status:

## Intended Use

- Decision-support use cases:
- Geographic coverage:
- Known non-goals:
- When the site should abstain:

## Data and Feature Contract

- Feature table version:
- Label definition:
- Trigger-oriented features:
- Structural-context features:
- Optional structural prior input:
- Structural provenance:
- Known data exclusions:
- Leakage protections:

## Training and Validation

- Baselines compared:
- Walk-forward split policy:
- Calibration method:
- Promotion gate:
- Threshold selection policy:
- Trigger-vs-prior handoff rule:
- Seed / reproducibility settings:

## Performance Summary

- Precision:
- Recall:
- F1:
- PR-AUC:
- ROC-AUC:
- Brier score:
- Precision@10:
- Recall@5:
- Recall@10:
- Episode recall:
- Median lead days:
- False alerts per true alert:
- No-clear-leader rate:

## Thresholds and Publication

- Publish threshold:
- Warning threshold:
- Alert threshold:
- Separation margin:
- Monitoring-only rule:
- No-clear-leader rule:

## Explainability

- Global feature importance source:
- Per-prediction driver method:
- Analyst caveats:

## Risks and Limitations

- Regions with weak coverage:
- Target-specific blind spots:
- Important missing indicators:
- Failure modes to monitor:
- Conditions under which baseline still wins:
