# AGENTS.md

Project: Flight Safety Risk Intelligence Platform

## Goal
Build a portfolio-grade aviation safety analytics platform aligned to a Flight Safety Data Science internship. The system should help analyze trends, support investigations, monitor fatigue-related signals, and communicate insights through Tableau dashboards.

## Dataset Rules
Use only public or clearly synthetic data.
Approved sources:
- BTS On-Time / Delay data as operational proxy
- NASA ASRS as voluntary safety-report and fatigue proxy
- NTSB aviation investigation data as investigation source
- FAASTeam event data as safety-promotion proxy
- Synthetic internal training / safety culture data for demonstration

Never claim access to confidential airline FOQA, ASAP, or internal SMS data.
Whenever a proxy is used, label it clearly in code comments, README, and docs.

## Required Stack
- Python for ingestion, ETL, NLP, feature engineering, and machine learning
- SQL / Teradata-style modeling for warehouse tables and marts
- R for statistical analysis and time-series validation
- Tableau-ready outputs for dashboards
- AWS-style raw / trusted / analytics data layering

## Architecture Rules
Maintain these folders:
- /data/raw
- /data/trusted
- /data/analytics
- /src/ingest
- /src/transform
- /src/features
- /src/models
- /sql
- /notebooks
- /docs
- /dashboards

## Quality Rules
- Use modular production-style code
- Add logging and basic validation
- Standardize columns to snake_case
- Include null checks, duplicate checks, and schema validation where practical
- Write concise comments and docstrings
- Keep everything interview-defensible and truthful

## Security and Privacy
- Treat safety narratives and event text as sensitive
- Mask or avoid exposing identifiers in downstream outputs
- Separate raw, trusted, and analytics layers
- Keep role-based / audience-based thinking in dashboard design
- Mention privacy and least-privilege concepts in project docs

## Deliverables
The repo should ultimately include:
- data ingestion scripts
- cleaned trusted tables
- SQL schema and marts
- feature engineering and NLP
- one or more ML examples
- R-based statistical analysis
- Tableau-ready datasets
- README
- architecture overview
- dashboard spec
- resume bullets
- interview talking points

## Output Standard
Every major task should produce:
1. runnable code
2. short explanation of assumptions
3. files placed in the correct folder
4. updates to README or docs if the task changes the project structure