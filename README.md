# Flight Safety Risk Intelligence Platform

## Project Goal
Build a portfolio-grade aviation safety analytics platform aligned to a Flight Safety Data Science internship. The project is designed to analyze operational and safety trends, support investigation-oriented workflows, surface fatigue-related proxy signals, and publish Tableau-ready outputs using only public or synthetic data.

## Datasets
- BTS On-Time / Delay data as an operational reliability proxy
- NASA ASRS safety reports as a voluntary reporting and fatigue proxy
- NTSB aviation investigation data for event and severity context
- FAASTeam event data as a safety-promotion proxy
- Synthetic training and safety culture data for demonstration

## Important Data Boundaries
- This repository does not use confidential airline FOQA, ASAP, or internal SMS data.
- Any proxy dataset is labeled clearly in code, documentation, and downstream outputs.
- Safety narratives and text fields should be treated as sensitive and restricted to the minimum required audience.

## Architecture
The project follows an AWS-style medallion flow:

1. `data/raw` stores source-aligned extracts from approved public or synthetic datasets.
2. `data/trusted` stores standardized, validated, and privacy-aware cleaned tables.
3. `data/analytics` stores feature tables, marts, and model-ready outputs for Tableau and analysis.

Code is organized by pipeline responsibility:
- `src/ingest` for source ingestion and raw layer loading
- `src/transform` for trusted-layer standardization and data quality checks
- `src/features` for feature engineering and model dataset construction
- `src/models` for risk modeling examples and evaluation summaries
- `src/common` for configuration, logging, and validation utilities

SQL assets are split into:
- `sql/schema` for warehouse-style table definitions
- `sql/marts` for analytics-facing marts and KPI logic

## Current Scaffold
- `config.yaml` centralizes dataset paths, metadata, and output locations
- `requirements.txt` defines the core Python stack
- Starter Python modules provide an opinionated pipeline layout
- Starter SQL files define trusted schemas and analytics marts
- Local demo outputs are written as CSV to keep setup lightweight
- `docs/architecture_overview.md` documents the system design and privacy posture

## How To Use
1. Create a virtual environment and install `requirements.txt`.
2. Generate local sample datasets with `python3 -m src.ingest.generate_sample_data`.
3. Place approved public or synthetic source files into the `data/raw` layer when you are ready to replace the samples.
4. Run ingestion, transformation, feature, and model modules in sequence. For the local demo, trusted and analytics layer outputs are written as CSV files.
5. Use the trusted and analytics outputs as inputs for SQL marts, notebooks, R analysis, or Tableau dashboards.

## Real Public-Data Build
The repo also supports a real public-data build with a requested 15-month portfolio horizon ending on `2026-02-28`.

Use these windows:
- Source-native supplemental window: `2024-12-01` through `2026-02-28` where the public source supports it
- Planned integrated cross-source dashboard window: calendar year `2025`
- Current verified executable integrated dashboard window as of `2026-03-24`: `2025-01-01` through `2025-11-30`

Why the integrated cross-source window is currently capped below the requested 15-month horizon:
- The integrated dashboard depends on BTS On-Time data as the public operational layer.
- As of March 24, 2026, the official BTS Reporting Carrier On-Time Performance profile shows `Latest Available Data: November 2025`.
- That means the project should not currently claim an integrated cross-source dashboard through `2026-02-28`, or even through `2025-12-31`, until a December 2025 BTS month is officially available.
- The broader 15-month range should therefore be handled as source-native supplemental analysis where coverage exists.

Real-data acquisition and rebuild runbook:
- Review `docs/real_data_acquisition_checklist.md`
- Place raw public files in the expected `data/raw` folders
- Rebuild the trusted layer with `python3 -m src.transform.build_trusted_layer`
- Rebuild analytics marts with `python3 -m src.features.build_analytics_marts`
- Refresh Tableau dashboards from the rebuilt analytics outputs

## Jan-Feb 2025 Real-Data Pilot
The current pilot scope is intentionally narrow and uses:
- Real BTS monthly files for January and February 2025
- One real NASA ASRS export covering January and February 2025
- Real NTSB source files for the same pilot period, using a CSV intermediate if MDB direct ingestion is not practical in the local environment
- Synthetic safety culture remains in place for the pilot
- FAASTeam manual extraction is deferred for this pilot, so the safety-promotion proxy remains synthetic / placeholder-oriented

For the NTSB pilot specifically:
- If the raw source is only `ntsb_aviation_avall.mdb` or the zipped MDB, extract an official CSV intermediate outside the project environment and place it in `data/raw/ntsb_investigations`
- The NTSB adapter will use CSV files directly and warn clearly when only MDB/ZIP files are present

## Local Sample Data
The repo includes a small synthetic generator so the pipeline can run end to end without external downloads.

Run:

```bash
python3 -m src.ingest.generate_sample_data
python3 -m src.transform.build_trusted_layer
python3 -m src.features.build_analytics_marts
python3 -m src.features.build_safety_features
python3 -m src.models.train_risk_model
```

Local demo outputs:
- `data/trusted/trusted_bts_on_time_operations.csv`
- `data/trusted/trusted_nasa_asrs_reports.csv`
- `data/trusted/trusted_ntsb_aviation_investigations.csv`
- `data/trusted/trusted_safety_events.csv`
- `data/analytics/monthly_risk_overview.csv`
- `data/analytics/fatigue_theme_trends.csv`
- `data/analytics/investigation_trends.csv`
- `data/analytics/operational_disruption_summary.csv`
- `data/analytics/safety_promotion_summary.csv`
- `data/analytics/safety_risk_features.csv`
- `data/analytics/model_training_dataset.csv`
- `data/analytics/risk_model_summary.json`

Generated raw samples include:
- `data/raw/operations/operations_sample.csv`
- `data/raw/incidents/incidents_sample.csv`
- `data/raw/investigations/investigations_sample.csv`
- `data/raw/safety_promotion/safety_promotion_sample.csv`
- `data/raw/synthetic_safety_culture/synthetic_safety_culture_monthly.csv`

The sample files intentionally include a few nulls, duplicates, and category variations so validation behavior can be demonstrated during development and interviews.
For the polished version of the project, CSV outputs can be upgraded back to Parquet once the environment and packaging story are finalized.
The demo model treats numeric and categorical fields differently, excludes identifier and source-tracking columns from baseline training, and avoids using `severity_score` as an input because it defines the current proxy target.
Run the main trusted-layer workflow with `python3 -m src.transform.build_trusted_layer`; it now produces `data/trusted/trusted_safety_events.csv`, and when source files are present it also produces `data/trusted/trusted_bts_on_time_operations.csv`, `data/trusted/trusted_nasa_asrs_reports.csv`, and `data/trusted/trusted_ntsb_aviation_investigations.csv`.
Run the integrated analytics workflow with `python3 -m src.features.build_analytics_marts` to create Tableau-ready proxy-driven outputs in `data/analytics`.
The Tableau-ready analytics outputs are `monthly_risk_overview.csv`, `fatigue_theme_trends.csv`, `investigation_trends.csv`, `operational_disruption_summary.csv`, and `safety_promotion_summary.csv`.
Recommended dashboard build order: `Monthly Risk Overview` first, then `Operational Disruption Summary`, `Fatigue Theme Trends`, `Investigation Trends`, and `Safety Promotion Summary`.
Use `docs/monthly_risk_overview_build_guide.md` as the step-by-step starting point for Dashboard 1, which is the primary interview showcase dashboard.
Run the standalone BTS adapter with `python3 -m src.transform.build_bts_trusted_layer` to create `data/trusted/trusted_bts_on_time_operations.csv` from raw files in `data/raw/bts_on_time`.
Run the standalone NTSB adapter with `python3 -m src.transform.build_ntsb_trusted_layer` to create `data/trusted/trusted_ntsb_aviation_investigations.csv` from raw files in `data/raw/ntsb_investigations`.

## Interview Talking Points
- Why public proxies were chosen instead of confidential airline systems
- How the raw, trusted, and analytics layers reduce quality and privacy risk
- Why shared validation and logging utilities were added early
- How the code structure supports future growth into NLP, R-based analysis, and dashboards

## Roadmap
- Add concrete dataset-specific ingestion adapters for BTS, ASRS, NTSB, and FAASTeam
- Add schema-specific validation rules and richer quality monitoring
- Add NLP pipelines for narrative classification and fatigue signal extraction
- Add baseline and interpretable ML models with model cards
- Add R scripts for time-series validation and statistical monitoring
- Add Tableau-ready marts and dashboard specifications
