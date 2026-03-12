# NTSB Adapter Notes

## Source Purpose
NTSB aviation investigation data is used in this project as a public investigation source that provides event severity context, occurrence types, and post-event perspective for safety trend analysis. It helps demonstrate how external investigation records can complement operational and reporting proxies without overstating coverage.

## Key Columns
- `ntsb_event_id`
- `event_date`
- `airport_code`
- `operator_name`
- `injury_severity`
- `event_type`
- `aircraft_damage`
- `source_system`

## Quality Risks
- Investigation extracts can contain missing operator, airport, or aircraft-damage values.
- Event coding may differ between preliminary and final records or across source vintages.
- Duplicate rows can appear when extracts are merged or refreshed.
- Investigation dates and closure timelines may not align with operational activity windows.
- Low event counts at fine grain can make comparisons unstable or misleading.

## Join Strategy
- Do not join NTSB events directly to BTS flight-leg records or synthetic employee-level data.
- Use NTSB primarily as a monthly, airport-level, operator-group, or occurrence-category context source.
- Join NTSB outputs to other sources through aggregated dimensions such as month, airport, region, or operator grouping.
- Preserve source-native event IDs in the trusted layer for auditability and traceability.

## Investigation Limitations
- NTSB records represent investigated events, not the full universe of operational safety observations.
- Investigations often involve significant lag between event occurrence and final characterization.
- Public investigation data is useful for severity context, but it should not be treated as a real-time monitoring feed.
- Small sample sizes can overemphasize rare event categories if used without aggregation.

## Why NTSB Is An Investigation Source And Not An Airline-Internal Safety System
NTSB data is a public investigation source focused on aviation events that warrant external investigation or documented follow-up. It is not equivalent to confidential airline-internal safety systems such as FOQA, ASAP, or SMS reporting pipelines, which capture different signals, different coverage levels, and different operational context. This project uses NTSB truthfully as an external investigation context source rather than claiming internal airline visibility.
