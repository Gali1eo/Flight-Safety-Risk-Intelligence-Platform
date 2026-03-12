# Tableau Data Dictionary

## Purpose
These analytics outputs are designed for Tableau dashboards and portfolio storytelling. Every output is built from public data or synthetic data only. Where a metric reflects operational pressure, fatigue signals, or safety culture, it should be described as proxy-driven unless it comes from a direct public investigation count.

## Output Files

### `monthly_risk_overview.csv`
Integrated monthly airport-level overview that combines public BTS operational context, public ASRS reporting volume, public NTSB investigation context, and synthetic safety-culture indicators.

Key fields:
- `report_month`: Reporting month in `YYYY-MM`
- `airport`: Airport or base-location aggregation key
- `region`: Coarse region derived from airport mapping
- `operational_flight_legs`: Public BTS flight-leg count
- `cancelled_flights`: Public BTS cancellation count
- `diverted_flights`: Public BTS diversion count
- `avg_departure_delay_minutes`: Average BTS departure delay
- `avg_arrival_delay_minutes`: Average BTS arrival delay
- `asrs_report_count`: Public ASRS report count
- `fatigue_related_report_count`: ASRS report count where human factors mention fatigue
- `ntsb_investigation_count`: Public NTSB investigation count
- `serious_or_higher_investigation_count`: NTSB investigations normalized to serious or fatal outcomes
- `avg_training_completion_rate`: Average synthetic training completion rate
- `avg_safety_engagement_score`: Average synthetic safety-engagement score
- `fatigue_training_completion_rate`: Average synthetic fatigue-training flag rate
- `synthetic_elevated_risk_count`: Count of synthetic safety-culture rows with `severity_score > 0`
- `data_basis`: Plain-language statement describing the public-data and proxy basis

### `fatigue_theme_trends.csv`
Public ASRS monthly summary for fatigue and other human-factor themes.

Key fields:
- `report_month`
- `airport`
- `carrier`
- `region`
- `human_factor_theme`
- `fatigue_related_flag`
- `report_count`
- `unique_anomaly_count`
- `data_basis`

### `investigation_trends.csv`
Public NTSB monthly summary of investigation activity, normalized severity, and occurrence categories.

Key fields:
- `report_month`
- `airport`
- `operator_group`
- `region`
- `investigation_category`
- `severity_normalized`
- `investigation_count`
- `serious_or_higher_count`
- `data_basis`

### `operational_disruption_summary.csv`
Public BTS monthly operational summary by carrier and route.

Key fields:
- `report_month`
- `carrier`
- `origin_airport`
- `destination_airport`
- `route`
- `region`
- `flight_leg_count`
- `cancelled_flight_count`
- `diverted_flight_count`
- `avg_departure_delay_minutes`
- `avg_arrival_delay_minutes`
- `cancellation_rate`
- `diversion_rate`
- `data_basis`

### `safety_promotion_summary.csv`
Public FAASTeam monthly summary of outreach volume by state, region, topic, and audience.

Key fields:
- `report_month`
- `state`
- `region`
- `topic`
- `audience_type`
- `event_count`
- `data_basis`

## KPI Definitions
- `Cancellation Rate`: `cancelled_flight_count / flight_leg_count`
- `Diversion Rate`: `diverted_flight_count / flight_leg_count`
- `Fatigue Related Report Count`: Count of ASRS reports whose `human_factors` field contains `fatigue`
- `Serious Or Higher Investigation Count`: Count of NTSB investigations whose normalized severity is `serious_injury` or `fatal_injury`
- `Synthetic Elevated Risk Count`: Count of synthetic safety-culture rows where `severity_score > 0`

## Proxy Caveats
- BTS metrics are operational disruption proxies and are not FOQA or flight data monitoring outputs.
- ASRS metrics are voluntary self-report proxies and are not equivalent to ASAP or a complete airline safety-reporting ledger.
- NTSB metrics reflect investigated public events and are not internal airline SMS monitoring.
- Synthetic safety-culture metrics are fabricated for demonstration and must never be described as real employee or airline data.
- FAASTeam metrics represent public outreach activity and are not internal training completion records.

## Dashboard Guidance
- Prefer month, airport, route, carrier, or region as the primary slice dimensions.
- Avoid presenting cross-source links as exact event-level matches.
- Use titles and captions that say `public-data-based`, `proxy-driven`, or `synthetic` where relevant.
