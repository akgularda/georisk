# Forecasting Model Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first working forecasting subsystem with configs, tests, train/calibrate/predict/explain CLIs, and synthetic local data.

**Architecture:** The package will keep forecast contracts explicit. Labels and splits are config-driven, model training is time-aware, and explainability artifacts are derived from saved models rather than recomputed ad hoc in other layers.

**Tech Stack:** Python, pandas, scikit-learn, LightGBM, pydantic, pytest, parquet

---

### Task 1: Lock contracts with tests

**Files:**
- Create: `src/tests/forecasting/test_contracts.py`
- Create: `src/tests/forecasting/test_labels.py`
- Create: `src/tests/forecasting/test_pipeline_integration.py`

**Step 1:** Write failing tests for target registry, horizon registry, label logic, time-split integrity, and end-to-end artifact generation.

**Step 2:** Run `pytest src/tests/forecasting -q` and confirm failures are caused by missing forecasting modules.

### Task 2: Implement minimal forecasting package

**Files:**
- Create: `src/forecasting/*.py`
- Create: `src/common/logging.py`

**Step 1:** Add schemas, targets, horizons, labels, dataset utilities, metrics, registry, training, calibration, prediction, and explanation modules.

**Step 2:** Re-run tests and fill the smallest gaps until the contract tests pass.

### Task 3: Add configs and fixture data

**Files:**
- Create: `configs/forecasting/*.yaml`
- Create: `data/fixtures/*.csv`

**Step 1:** Add sample configs for 7-, 30-, and 90-day country-day training.

**Step 2:** Add synthetic feature data and example prediction output.

### Task 4: Add docs and CI

**Files:**
- Create: `docs/forecasting.md`
- Create: `docs/model_card_template.md`
- Create: `.github/workflows/python-ci.yml`

**Step 1:** Document how to train, calibrate, predict, and explain locally.

**Step 2:** Add a narrow Python CI workflow that runs the forecasting tests.

