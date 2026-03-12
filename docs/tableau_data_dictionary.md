# Tableau Data Dictionary

## Purpose
These analytics outputs are designed for Tableau dashboards and portfolio storytelling. Every file is built from public data or synthetic data only. Any signal related to operational pressure, fatigue, culture, or safety promotion should be described as proxy-driven unless it is explicitly a public investigation count.

## Output Files

### `monthly_risk_overview.csv`
Business purpose:
Provide the primary interview showcase dashboard dataset by combining public operational pressure, public safety-report volume, public investigation context, and synthetic safety-culture indicators at a defensible monthly airport level.

Row grain:
One row per `report_month` x `airport`.

Dimensions:
- `report_month`
- `airport`
- `region`
- `data_basis`

Measures:
- `operational_flight_legs`
- `cancelled_flights`
- `diverted_flights`
- `avg_departure_delay_minutes`
- `avg_arrival_delay_minutes`
- `asrs_report_count`
- `fatigue_related_report_count`
- `ntsb_investigation_count`
- `serious_or_higher_investigation_count`
- `avg_training_completion_rate`
- `avg_safety_engagement_score`
- `fatigue_training_completion_rate`
- `synthetic_elevated_risk_count`

Proxy caveats:
- BTS fields represent public operational disruption context and are not FOQA or airline telemetry.
- ASRS fields represent voluntary public reporting and are not ASAP or a complete internal reporting ledger.
- NTSB fields represent public investigations, not real-time internal safety monitoring.
- Safety-culture measures are synthetic and should be labeled clearly as demonstration data.
- Cross-source alignment is monthly and airport-level only; it is not a record-level join.

### `fatigue_theme_trends.csv`
Business purpose:
Support a focused fatigue and human-factors dashboard showing where public voluntary reports concentrate by airport, carrier proxy, and theme.

Row grain:
One row per `report_month` x `airport` x `carrier` x `human_factor_theme`.

Dimensions:
- `report_month`
- `airport`
- `carrier`
- `region`
- `human_factor_theme`
- `fatigue_related_flag`
- `data_basis`

Measures:
- `report_count`
- `unique_anomaly_count`

Proxy caveats:
- Built from public ASRS voluntary reports only.
- `carrier` is a coarse public grouping derived from operator names where practical.
- Fatigue trends are reporting proxies, not verified fatigue events.
- Narrative themes should be framed as reported patterns, not system-of-record truths.

### `investigation_trends.csv`
Business purpose:
Show investigation volume, normalized severity, and category mix for public aviation investigations over time.

Row grain:
One row per `report_month` x `airport` x `operator_group` x `investigation_category` x `severity_normalized`.

Dimensions:
- `report_month`
- `airport`
- `operator_group`
- `region`
- `investigation_category`
- `severity_normalized`
- `data_basis`

Measures:
- `investigation_count`
- `serious_or_higher_count`

Proxy caveats:
- Investigation counts reflect public NTSB records only.
- Investigation timing can lag the actual operational event.
- `operator_group` is a simplified grouping to support storytelling, not a full airline master dimension.
- This file should be positioned as external investigation context, not internal SMS surveillance.

### `operational_disruption_summary.csv`
Business purpose:
Provide a route- and carrier-level public operational baseline for delay, cancellation, and diversion storytelling.

Row grain:
One row per `report_month` x `carrier` x `origin_airport` x `destination_airport` x `route`.

Dimensions:
- `report_month`
- `carrier`
- `origin_airport`
- `destination_airport`
- `route`
- `region`
- `data_basis`

Measures:
- `flight_leg_count`
- `cancelled_flight_count`
- `diverted_flight_count`
- `avg_departure_delay_minutes`
- `avg_arrival_delay_minutes`
- `cancellation_rate`
- `diversion_rate`

Proxy caveats:
- This is public BTS operations data, not FOQA, FDM, or internal dispatch telemetry.
- Delay and disruption patterns are operational proxies that may correlate with safety stress but do not directly measure safety performance.
- Route comparisons should be framed as public operational context only.

### `safety_promotion_summary.csv`
Business purpose:
Support a dashboard on public safety-promotion outreach volume, topic mix, and audience focus by state and region.

Row grain:
One row per `report_month` x `state` x `topic` x `audience_type`.

Dimensions:
- `report_month`
- `state`
- `region`
- `topic`
- `audience_type`
- `data_basis`

Measures:
- `event_count`

Proxy caveats:
- Built from public FAASTeam event listings only.
- Outreach event volume is a safety-promotion proxy and should not be equated with actual airline training completion.
- Geographic coverage is approximate and may not align cleanly to airport or carrier operations.

## KPI Definitions
- `Cancellation Rate`: `cancelled_flight_count / flight_leg_count`
- `Diversion Rate`: `diverted_flight_count / flight_leg_count`
- `Fatigue Related Report Count`: Count of ASRS rows where `fatigue_related_flag = 1`
- `Serious Or Higher Investigation Count`: Count of NTSB rows where normalized severity is `serious_injury` or `fatal_injury`
- `Synthetic Elevated Risk Count`: Count of synthetic safety-culture rows where `severity_score > 0`
- `Average Training Completion Rate`: Mean of synthetic `training_completion_rate`
- `Average Safety Engagement Score`: Mean of synthetic `safety_engagement_score`

## Global Proxy Caveats
- This project does not use airline-internal SMS, FOQA, ASAP, or confidential training datasets.
- Public and synthetic sources are integrated only at aggregate levels such as month, airport, carrier, route, and region.
- Cross-source stories should always be presented as contextual relationships, not causal proof or event-level traceability.

## Dashboard Guidance
- Use `monthly_risk_overview.csv` as the primary showcase dataset for interviews.
- Prefer titles and subtitles that say `public-data-based`, `proxy-driven`, or `synthetic` where relevant.
- Avoid exposing ASRS narrative text in broad-audience dashboards.
- Keep drill paths aggregate-first: month to region to airport to route or category.
