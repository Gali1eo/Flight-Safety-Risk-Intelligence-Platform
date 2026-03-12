# NASA ASRS Adapter Notes

## Source Purpose
NASA ASRS is used in this project as a public voluntary safety-report source for trend analysis, narrative exploration, and fatigue-related proxy signals. It helps demonstrate how safety narratives can be standardized and promoted into a trusted layer without implying access to confidential airline systems.

## Key Columns
- `report_id`
- `event_date`
- `location`
- `aircraft_operator`
- `anomaly`
- `human_factors`
- `narrative`
- `source_system`

## Quality Risks
- Reporting is voluntary, so the dataset is subject to underreporting and self-selection bias.
- Narrative text is unstructured and may contain inconsistent terminology or incomplete context.
- Some records may omit operator or location details.
- Duplicate extracts or repeated report IDs can appear when multiple raw files are combined.
- Public extracts may contain malformed or incomplete event dates that need validation.

## Join Strategy
- Do not join ASRS records directly to BTS flight legs or internal-style crew records.
- Use ASRS primarily at monthly, operator-group, airport, or theme level.
- Treat narrative-derived features and fatigue-related counts as contextual indicators rather than exact event matches.
- Preserve the source-native `report_id` in the trusted layer for traceability inside the project.

## Privacy-Aware Handling
- The trusted ASRS adapter preserves the `narrative` field because narrative text is central to later NLP and qualitative review.
- Even though ASRS is public, narratives should still be treated as sensitive in downstream analytics because they can contain operational detail or contextual clues.
- Dashboard and broad-audience outputs should prefer aggregates, themes, counts, or masked excerpts instead of raw narratives.

## Why ASRS Is A Proxy And Not ASAP Data
ASRS is a public NASA-managed voluntary reporting system. ASAP, by contrast, is an airline-specific safety reporting program that is not publicly available in the same way and may contain confidential operational context. This project uses ASRS as a truthful proxy for self-reported safety and fatigue themes, but it should never claim that ASRS is equivalent to actual ASAP data or a complete airline safety reporting system.
