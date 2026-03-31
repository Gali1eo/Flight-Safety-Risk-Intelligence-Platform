# Flight Safety Risk Intelligence Platform

## Overview
Flight Safety Risk Intelligence Platform is an end-to-end aviation analytics project built with public and synthetic data. It combines operational disruption data, voluntary safety reports, investigation context, and fatigue-related narrative analysis through a raw → trusted → analytics pipeline and Tableau dashboards.

## Public Data and Proxy Scope
This project does **not** use confidential airline FOQA, ASAP, or internal Safety Management System data.

Instead, it uses clearly labeled public or synthetic proxies:
- **BTS On-Time / Delay** as an operational context proxy
- **NASA ASRS** as a voluntary safety-report and human-factors proxy
- **NTSB aviation investigation data** as investigation context
- **Synthetic safety-culture data** as a clearly labeled proxy for the pilot phase

All cross-source integration is aggregate-only and explicitly framed as proxy-based.

## Architecture
The repo follows a simple raw -> trusted -> analytics pattern:

- `data/raw` for source-aligned public and synthetic inputs
- `data/trusted` for standardized, validated, privacy-aware tables
- `data/analytics` for dashboard-ready marts, model outputs, and summaries

Core stack:

- Python for ingest, ETL, NLP, feature engineering, and ML
- SQL for warehouse-style schema and marts
- Tableau for dashboards
- CSV-based local pilot workflow for reproducibility

## Pilot Scope And Sources
The final pilot is intentionally scoped to **January 2025 through February 2025**.

Public / proxy sources:

- **BTS On-Time / Delay** for operational disruption context
- **NASA ASRS** for voluntary safety-report and fatigue proxy signals
- **NTSB aviation investigations** for external investigation context
- **FAASTeam** for safety-promotion proxy context
- **Synthetic safety culture** for demonstration-only culture and training proxies

# Flight Safety Risk Intelligence Platform


## Dashboard Summary
### Dashboard 1: Monthly Risk Overview
Shows month-level operational risk context across the pilot window, including BTS activity, ASRS report volume, investigation context, and airport-level concentration.

### Dashboard 2: Investigation Trends
Shows NTSB investigation volume, category mix, and severity context across the pilot window. It demonstrates how public investigation data can complement operational proxies without implying internal airline access.

### Dashboard 3: Fatigue Theme Trends
Shows ASRS-derived fatigue and human-factor themes. This dashboard is intentionally frozen in a limited refreshed state after model enrichment. It should be treated as a pilot view, not a full redesign, and the fatigue signal remains proxy-based rather than ground truth.

## ASRS NLP And Fatigue Modeling
The ASRS pipeline is built around the trusted Jan-Feb 2025 pilot extract and keeps the schema truthful by using the trusted `location` and `aircraft_operator` equivalents present in the source file.

### Rule-Based Baseline
The first NLP layer is a transparent ASRS baseline built on `narrative_clean`. It produces:

- `narrative_clean`
- `fatigue_keyword_flag`
- `fatigue_keyword_count`
- `fatigue_confidence_tier`
- `weak_fatigue_label`
- `theme_fatigue_flag`
- `theme_communication_flag`
- `theme_distraction_flag`
- `theme_workload_flag`
- `theme_procedure_checklist_flag`
- `theme_ground_taxi_conflict_flag`
- `theme_approach_landing_instability_flag`
- `theme_primary_label`

### Benchmark 1
TF-IDF plus class-balanced logistic regression on `narrative_clean` only.

- 3-fold stratified cross-validation
- Proxy target: `weak_fatigue_label`
- OOF positive metrics: precision `0.0526`, recall `0.1667`, F1 `0.08`
- Average precision: `0.0299`
- ROC AUC: `0.6083`
- Confusion matrix: `614 TN / 36 FP / 10 FN / 2 TP`

### Benchmark 2
TF-IDF plus the engineered narrative fatigue features from `src/features/build_asrs_fatigue_features.py`.

- 3-fold stratified cross-validation
- Same proxy target: `weak_fatigue_label`
- OOF positive metrics: precision `0.9`, recall `0.75`, F1 `0.8182`
- Average precision: `0.7775`
- ROC AUC: `0.8574`
- Confusion matrix: `649 TN / 1 FP / 3 FN / 9 TP`

### Why Benchmark 2 Was Selected
Benchmark 2 won on the primary imbalance-aware metric, average precision, and also delivered a large positive F1 gain. It is the selected model for the pilot release because it is still lightweight and interpretable, but materially better than the text-only baseline.

## Release Artifacts
The current public outputs are written to `data/analytics` and are ready for downstream analysis or Tableau enrichment.

- `data/analytics/asrs_nlp_enriched.csv`
- `data/analytics/asrs_fatigue_features.csv`
- `data/analytics/asrs_fatigue_model_summary.json`
- `data/analytics/asrs_fatigue_predictions.csv`
- `data/analytics/asrs_fatigue_model_comparison.json`
- `data/analytics/asrs_nlp_scored.csv`
- `data/analytics/asrs_fatigue_summary_by_month.csv`
- `data/analytics/asrs_fatigue_summary_by_operator.csv`
- `data/analytics/asrs_fatigue_summary_by_location.csv`
- `data/analytics/asrs_fatigue_summary_by_theme.csv`
- `docs/dashboard_exports/dashboard_1_monthly_risk_overview.png`
- `docs/dashboard_exports/dashboard_2_investigation_trends.png`
- `docs/dashboard_exports/dashboard_3_fatigue_theme_trends.png`
- `docs/pilot_release_manifest.json`

The compact release manifest is included for quick portfolio review and machine-readable inventory.

## How To Re-Run
From the project root:

```bash
source .venv/bin/activate
python -m src.transform.build_trusted_layer
python -m src.features.build_analytics_marts
python -m src.features.build_asrs_nlp_baseline
python -m src.features.build_asrs_fatigue_features
python -m src.models.train_asrs_fatigue_benchmark
python -m src.models.train_asrs_fatigue_hybrid_benchmark
```

## Key Caveats

- This is a **public-data-based, proxy-driven** project.
- ASRS is a voluntary reporting source and is not equivalent to ASAP.
- BTS is an operational proxy and not FOQA.
- Model-enriched fatigue signals are **not** ground truth fatigue labels.
- NTSB records provide external investigation context and may lag event timing.
- Synthetic safety-culture data is clearly labeled and used only where a truthful public substitute was not practical in this pilot.

## Future Enhancements

- Expand the pilot window beyond Jan-Feb 2025 after additional validation
- Add more public-source coverage where it remains defensible
- Add R-based validation once the pilot scope broadens
- Refresh Dashboard 3 only after any further model or scope expansion
