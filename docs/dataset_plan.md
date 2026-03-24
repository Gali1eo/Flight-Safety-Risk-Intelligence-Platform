# Dataset Acquisition And Join Plan

## Purpose
This document defines how each approved dataset contributes to the project, where raw files are expected to land, what level of detail each source represents, and how sources can be combined truthfully. The goal is to keep the project interview-defensible by being explicit about proxies, join limits, and data quality tradeoffs.

## Integration Principles
- Public sources in this repo should usually be combined at aggregate levels such as month, airport, carrier, route, operator group, or region.
- The project should not imply that BTS flights, ASRS reports, NTSB investigations, and FAASTeam events can be perfectly linked record by record.
- Synthetic internal training and safety culture data exists only to demonstrate how internal indicators could be modeled in a privacy-safe portfolio project.
- Any dashboard or model output should state clearly when a metric comes from a proxy rather than a direct safety system of record.

## Real-Data Window Design
- Requested portfolio horizon: `2024-12-01` through `2026-02-28`
- Planned integrated cross-source dashboard window: calendar year `2025`
- Current verified executable integrated window as of `2026-03-24`: `2025-01-01` through `2025-11-30`
- Source-native supplemental window: `2024-12-01` through `2026-02-28` where each source supports it

Why the integrated window is capped:
- The public BTS Reporting Carrier On-Time dataset is the operational backbone for the integrated cross-source dashboards.
- As of March 24, 2026, the official BTS TranStats page for Reporting Carrier On-Time Performance shows `Latest Available Data: November 2025`.
- Because of that official public-data limit, the project should not currently claim a fully BTS-backed integrated dashboard through February 2026, or even through December 2025, until the December 2025 BTS month is officially available.
- The broader December 2024 through February 2026 range is still useful for source-native supplemental analysis in ASRS, NTSB, and FAASTeam views.

## Source Plan

### BTS On-Time / Delay Data
- Purpose in project: Provide an operational performance baseline for delays, cancellations, diversions, route pressure, and airport disruption trends.
- Real public data or proxy: Real public data used as an operational proxy for stressors that may correlate with safety risk, not as a direct safety event source.
- Expected file format: CSV extracts, typically partitioned by month.
- Expected grain: One row per flight leg.
- Key columns:
  - `flight_date`
  - `reporting_airline`
  - `flight_number`
  - `origin`
  - `dest`
  - `dep_delay`
  - `arr_delay`
  - `cancelled`
  - `diverted`
- Join strategy:
  - Do not claim direct joins to ASRS or NTSB records at the individual event level.
  - Aggregate first by `event_month`, `reporting_airline`, `origin`, `dest`, or route family.
  - Use BTS-derived monthly operational pressure indicators as context features alongside safety-report aggregates.
- Main data quality risks:
  - Monthly schema changes or renamed columns across download periods
  - Partial records for cancelled or diverted operations
  - Carrier mergers, rebrands, or code changes that can distort trend lines
  - Missing or inconsistent identifiers for route normalization

### NASA ASRS
- Purpose in project: Provide safety-report narratives and fatigue-related proxy signals for trend analysis, NLP, and event theme tracking.
- Real public data or proxy: Real public data used as a safety-report and fatigue proxy, not as a complete record of all safety events.
- Expected file format: CSV extracts from public ASRS data downloads.
- Expected grain: One row per submitted report.
- Key columns:
  - `report_id`
  - `event_date`
  - `location`
  - `aircraft_operator`
  - `narrative`
  - `anomaly`
  - `human_factors`
- Join strategy:
  - Avoid record-level joins to BTS flight legs because ASRS reporting is voluntary and often anonymized.
  - Aggregate by month, operator grouping, airport or location, narrative theme, or fatigue-related keyword flags.
  - Use ASRS counts and text-derived signals as safety context features rather than exact matches.
- Main data quality risks:
  - Underreporting and self-selection bias
  - Free-text narrative variability and inconsistent terminology
  - Missing, redacted, or non-standardized location and operator fields
  - Duplicate semantic events represented through multiple reports

### NTSB Aviation Investigation Data
- Purpose in project: Add event severity, occurrence categories, and investigation context to long-term safety trend analysis.
- Real public data or proxy: Real public data representing investigated events, but still not a complete operational safety ledger.
- Expected file format: CSV extracts from public aviation investigation datasets.
- Expected grain: One row per investigation or event record, depending on the extract.
- Key columns:
  - `ntsb_event_id`
  - `event_date`
  - `airport_code`
  - `operator_name`
  - `injury_severity`
  - `event_type`
  - `aircraft_damage`
- Join strategy:
  - Treat NTSB as a severity context source rather than a direct join target for every BTS or ASRS record.
  - Aggregate by month, airport, operator group, or event type.
  - Use NTSB rates and severity summaries to contextualize operational or reporting trends at the same aggregate grain.
- Main data quality risks:
  - Long lags between occurrence date and investigation closure
  - Missing operator or airport details for some records
  - Differences between preliminary and final coding
  - Low event counts that can make granular comparisons unstable

### FAASTeam Event Data
- Purpose in project: Measure safety outreach activity and approximate safety-promotion exposure by geography and time period.
- Real public data or proxy: Real public data used as a safety-promotion proxy, not as evidence of internal training completion.
- Expected file format: CSV extracts or manually consolidated CSV files from public event listings.
- Expected grain: One row per FAASTeam event.
- Key columns:
  - `event_id`
  - `event_date`
  - `location`
  - `state`
  - `topic`
  - `audience_type`
- Join strategy:
  - Join only at aggregate levels such as month, state, metro area, or airport catchment where defensible.
  - Use event counts and topic mix as leading indicators of outreach intensity.
  - Keep FAASTeam analysis separate from internal training metrics unless clearly labeled as conceptually related but not equivalent.
- Main data quality risks:
  - Manual extraction may introduce formatting inconsistency
  - Duplicate postings or updates for the same event
  - Weak mapping from city-level event data to airport or carrier operations
  - Topic labels may need standardization before analysis

### Synthetic Internal Training / Safety Culture Data
- Purpose in project: Demonstrate how an internal airline-style safety culture or training dataset could be integrated without implying access to confidential systems.
- Real public data or proxy: Synthetic data only. It is a proxy for internal training completion, engagement, and culture indicators.
- Expected file format: CSV generated locally for the project.
- Expected grain: One row per employee-period, crew-period, or base-period, depending on the synthetic design.
- Key columns:
  - `employee_period_key`
  - `period_start_date`
  - `base_location`
  - `fleet_group`
  - `training_completion_rate`
  - `safety_engagement_score`
  - `fatigue_training_flag`
- Join strategy:
  - Do not join synthetic employee keys to public records.
  - Join only to synthetic dimensions or to external aggregates by month, base location, or fleet proxy where the relationship is explicitly conceptual.
  - Use this source to demonstrate feature engineering and privacy-aware modeling patterns, not to imply real internal visibility.
- Main data quality risks:
  - Unrealistic synthetic distributions if generation logic is too simple
  - False confidence from synthetic keys that look production-grade
  - Overstating interpretability of culture metrics without a clear synthetic-data disclaimer
  - Synthetic location and fleet mappings may not align neatly with public source dimensions

## Recommended Join Design
The safest and most defensible integration pattern is a layered join strategy:

1. Standardize each source independently into trusted tables with source-native keys preserved.
2. Build conformed dimensions for `calendar_month`, `airport_or_location`, `carrier_or_operator_group`, and `region`.
3. Aggregate each source into monthly fact tables at the lowest defensible common grain.
4. Join aggregated facts into analytics marts for Tableau and modeling features.

Recommended examples:
- BTS monthly delay metrics by carrier-airport-route
- ASRS monthly fatigue and anomaly counts by airport or operator group
- NTSB monthly severity counts by airport or operator group
- FAASTeam monthly outreach counts by state, city, or airport catchment
- Synthetic training and culture metrics by base location and month

## Acquisition Notes
- Save raw files in the exact source-specific folders defined in `config.yaml`.
- Preserve original source extracts in the raw layer before standardization.
- Document download date, source URL, and any manual extraction steps in future ingestion modules or docs.
- Where a public source is hard to automate, note the manual step rather than pretending the ingestion is fully automated.
- Use `docs/real_data_acquisition_checklist.md` as the operational runbook for real public-data acquisition and rebuild order.
