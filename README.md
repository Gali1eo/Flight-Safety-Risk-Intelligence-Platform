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
- `docs/architecture_overview.md` documents the system design and privacy posture

## How To Use
1. Create a virtual environment and install `requirements.txt`.
2. Place approved public or synthetic source files into the `data/raw` layer.
3. Run ingestion, transformation, feature, and model modules in sequence.
4. Use the trusted and analytics outputs as inputs for SQL marts, notebooks, R analysis, or Tableau dashboards.

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
