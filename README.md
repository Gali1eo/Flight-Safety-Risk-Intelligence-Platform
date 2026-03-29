# Flight Safety Risk Intelligence Platform

## Project Goal
Build a portfolio-grade flight safety analytics platform aligned to a Flight Safety Data Science internship using only public and synthetic data. The project analyzes operational trends, voluntary safety-report signals, investigation patterns, and fatigue-related human-factor themes through a raw → trusted → analytics pipeline and Tableau dashboards.

## Public-Data / Proxy Disclaimer
This project does **not** use confidential airline FOQA, ASAP, or internal Safety Management System data.

Instead, it uses clearly labeled public or synthetic proxies:
- **BTS On-Time / Delay** as an operational / FOQA-style proxy
- **NASA ASRS** as a voluntary safety-report / fatigue / human-factors proxy
- **NTSB aviation investigation data** as investigation context
- **Synthetic safety-culture data** as a safety-culture proxy for the current pilot phase

All cross-source integration is aggregate-only and interview-defensible.

## Architecture
The platform follows an AWS-style layered design:

- **Raw layer**: source-aligned public and synthetic files
- **Trusted layer**: standardized, validated, privacy-aware outputs
- **Analytics layer**: dashboard-ready marts and summary datasets

Tech stack:
- **Python** for ingestion, transformation, feature engineering, and analytics
- **SQL / warehouse-style marts** for structured analytical modeling
- **Tableau** for dashboarding and presentation
- **CSV-based local pilot workflow** for easy reproducibility

## Data Sources
### 1. BTS On-Time / Delay
Used as the operational context layer for flight volume, delays, cancellations, and diversions.

### 2. NASA ASRS
Used as a public voluntary safety-report source for fatigue and human-factor themes.

### 3. NTSB Aviation Investigations
Used as external investigation and severity context.

### 4. Synthetic Safety Culture
Used in the current pilot as a clearly labeled synthetic proxy for safety culture / training indicators.

## Dashboard 1: Monthly Risk Overview
![Dashboard 1](docs/dashboard_exports/dashboard_1_monthly_risk_overview.png)

What it shows:
- operational flight volume across the Jan–Feb 2025 pilot window
- ASRS report activity and investigation context
- high-level KPI view for the pilot
- airport-level operational concentration

Why it matters:
This dashboard gives an interview-ready executive view of how public operational and safety proxies can be integrated into a monthly flight safety monitoring story.

## Dashboard 2: Investigation Trends
![Dashboard 2](docs/dashboard_exports/dashboard_2_investigation_trends.png)

What it shows:
- NTSB investigation counts across the pilot window
- investigation category distribution
- severity mix
- investigation trend context

Why it matters:
This dashboard demonstrates how public investigation data can be used to add external safety-event context without claiming internal airline monitoring access.

## Dashboard 3: Fatigue Theme Trends
![Dashboard 3](docs/dashboard_exports/dashboard_3_fatigue_theme_trends.png)

What it shows:
- ASRS-derived fatigue and human-factor theme signals
- top fatigue-related themes
- report concentration by carrier/theme grouping
- Jan–Feb 2025 trend movement

Why it matters:
This dashboard highlights how voluntary public safety reports can be used as a defensible fatigue and human-factors proxy.

## Current Pilot Scope
This public-data pilot currently covers:
- **January 2025**
- **February 2025**

The pilot was intentionally constrained to create a truthful, manageable first production-style portfolio version before expanding the historical window.

## Key Caveats
- This is a **public-data-based, proxy-driven** project.
- It does **not** represent internal airline operational telemetry.
- ASRS is a voluntary reporting source and is not equivalent to ASAP.
- BTS is an operational proxy and not FOQA.
- NTSB investigations are external records and may lag actual event timing.
- Synthetic safety-culture data is clearly labeled and used only where a truthful public substitute was not practical in this pilot phase.

## How to Re-run the Pipeline
From the project root:

```bash
source .venv/bin/activate
python -m src.transform.build_trusted_layer
python -m src.features.build_analytics_marts