# BTS Adapter Notes

## Source Purpose
BTS On-Time / Delay data is used in this project as a public operational proxy for delay pressure, cancellation exposure, route disruption, and airport-level operational stress. It helps approximate the kind of operational context that might be compared against safety signals, without claiming access to airline-internal telemetry.

## Key Columns
- `flight_date`
- `reporting_airline`
- `flight_number`
- `origin`
- `dest`
- `dep_delay`
- `arr_delay`
- `cancelled`
- `diverted`
- `tail_number`

## Grain
The expected grain is one row per flight leg in the public BTS extract.

## Quality Risks
- Monthly public files may change schemas or column names over time.
- Cancelled and diverted flights can have partial delay or aircraft fields.
- Carrier code changes, code-shares, or reporting differences can complicate longitudinal analysis.
- Duplicate rows may appear when monthly extracts are combined or reloaded.
- Public operational records do not provide the cockpit- or sensor-level fidelity associated with internal airline data.

## Join Strategy
- Do not join BTS flight legs directly to ASRS narratives or NTSB investigations at the individual record level.
- Use BTS primarily at monthly, airport, carrier, route, or region level.
- Build derived operational stress indicators such as delay rates, cancellation rates, and diversion rates before combining with other safety proxy sources.
- Preserve source-native fields and add normalized dimensions like `carrier`, `origin_airport`, `destination_airport`, and `route` for trustworthy aggregation.

## Why BTS Is An Operational Proxy And Not Real FOQA Data
BTS On-Time / Delay data is a public operational reporting source. FOQA, by contrast, is an airline-internal flight data monitoring program that uses much richer aircraft and operational telemetry, is not publicly available, and supports very different types of safety analysis. This project uses BTS truthfully as a public operational proxy for disruption and reliability context, not as a substitute for real FOQA data.
