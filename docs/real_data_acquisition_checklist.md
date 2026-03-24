# Real Data Acquisition Checklist

## Purpose
This runbook moves the project from the tiny synthetic demo into a real public-data build while staying truthful about source coverage and integration limits.

## Date Windows
- Requested portfolio horizon: `2024-12-01` through `2026-02-28`
- Source-native supplemental window: `2024-12-01` through `2026-02-28` where each public source supports it
- Planned integrated cross-source dashboard window: calendar year `2025-01-01` through `2025-12-31`
- Current verified executable integrated window as of `2026-03-24`: `2025-01-01` through `2025-11-30`

Why the executable integrated window currently stops at November 2025:
- The official BTS Reporting Carrier On-Time Performance dataset currently shows `Latest Available Data: November 2025` on TranStats as of March 24, 2026.
- That means a truthful integrated cross-source dashboard cannot yet claim a December 2025 BTS-backed operational layer.
- The project should therefore keep a clear distinction between:
  - the planning target for a full 2025 integrated dashboard
  - the currently runnable integrated build based on the latest officially available BTS month

## Raw Folder Expectations
- `data/raw/bts_on_time/`
  - Monthly BTS On-Time CSV files for 2025
  - Recommended pattern: `bts_on_time_2025_01.csv`, `bts_on_time_2025_02.csv`, and so on
- `data/raw/nasa_asrs/`
  - CSV exports from the public NASA ASRS database for the supplemental window
  - Keep export files date-scoped and name them clearly, for example `asrs_reports_2024_12_to_2025_02.csv`
- `data/raw/ntsb_investigations/`
  - Public NTSB aviation investigation extracts covering the supplemental window
  - Keep download dates and file provenance in the filename or a sidecar note
- `data/raw/faasteam_events/`
  - Public FAASTeam past-event CSV extracts or manually consolidated CSV files
  - Include download date in the filename when possible

## Official Source Starting Points
- BTS Reporting Carrier On-Time Performance:
  - `https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FGJ`
- NASA ASRS Database Online:
  - `https://asrs.arc.nasa.gov/search/database.html`
- NTSB Accident Data and CAROL:
  - `https://www.ntsb.gov/safety/data/pages/Data_Stats.aspx`
- FAASTeam Seminars and Webinars search:
  - `https://www.faasafety.gov/SPANS/events/EventList.aspx`

## Source-By-Source Acquisition Checklist

### BTS On-Time Monthly Files
Public source role:
- Public operational proxy for delays, cancellations, diversions, route disruption, and airport pressure

Coverage target:
- January 2025 through December 2025

Checklist:
- [ ] Download January 2025 BTS On-Time file
- [ ] Download February 2025 BTS On-Time file
- [ ] Download March 2025 BTS On-Time file
- [ ] Download April 2025 BTS On-Time file
- [ ] Download May 2025 BTS On-Time file
- [ ] Download June 2025 BTS On-Time file
- [ ] Download July 2025 BTS On-Time file
- [ ] Download August 2025 BTS On-Time file
- [ ] Download September 2025 BTS On-Time file
- [ ] Download October 2025 BTS On-Time file
- [ ] Download November 2025 BTS On-Time file
- [ ] Check whether December 2025 is officially available before claiming a full-year integrated dashboard

Truth note:
- As of March 24, 2026, the official BTS Reporting Carrier On-Time Performance profile shows `Latest Available Data: November 2025`, so December 2025 should be treated as pending verification rather than assumed present.

### NASA ASRS Exported CSV Files
Public source role:
- Public voluntary safety-report and fatigue proxy, not ASAP

Coverage target:
- December 2024 through February 2026 where public query results are available

Checklist:
- [ ] Export ASRS records for December 2024
- [ ] Export ASRS records for January 2025
- [ ] Export ASRS records for February 2025
- [ ] Export ASRS records for March 2025
- [ ] Export ASRS records for April 2025
- [ ] Export ASRS records for May 2025
- [ ] Export ASRS records for June 2025
- [ ] Export ASRS records for July 2025
- [ ] Export ASRS records for August 2025
- [ ] Export ASRS records for September 2025
- [ ] Export ASRS records for October 2025
- [ ] Export ASRS records for November 2025
- [ ] Export ASRS records for December 2025
- [ ] Export ASRS records for January 2026
- [ ] Export ASRS records for February 2026
- [ ] Split exports into multiple pulls if a query exceeds NASA ASRS export size limits

Operational note:
- NASA ASRS supports CSV export from the public ASRS Database Online.

### NTSB Aviation Investigation Data
Public source role:
- Public external investigation context source, not internal SMS

Coverage target:
- December 2024 through February 2026

Checklist:
- [ ] Pull NTSB aviation investigation records covering December 2024
- [ ] Pull NTSB aviation investigation records covering January 2025
- [ ] Pull NTSB aviation investigation records covering February 2025
- [ ] Pull NTSB aviation investigation records covering March 2025
- [ ] Pull NTSB aviation investigation records covering April 2025
- [ ] Pull NTSB aviation investigation records covering May 2025
- [ ] Pull NTSB aviation investigation records covering June 2025
- [ ] Pull NTSB aviation investigation records covering July 2025
- [ ] Pull NTSB aviation investigation records covering August 2025
- [ ] Pull NTSB aviation investigation records covering September 2025
- [ ] Pull NTSB aviation investigation records covering October 2025
- [ ] Pull NTSB aviation investigation records covering November 2025
- [ ] Pull NTSB aviation investigation records covering December 2025
- [ ] Pull NTSB aviation investigation records covering January 2026
- [ ] Pull NTSB aviation investigation records covering February 2026
- [ ] Preserve whether the extract came from CAROL, downloadable aviation accident files, or another official NTSB public extract

Operational note:
- NTSB publishes public aviation accident and investigation data, including downloadable aviation accident datasets and the CAROL search system.

### FAASTeam Past Events
Public source role:
- Public safety-promotion proxy, not airline-internal training completion

Coverage target:
- Past 15 months ending February 28, 2026

Checklist:
- [ ] Export or manually capture FAASTeam past events for December 2024
- [ ] Export or manually capture FAASTeam past events for January 2025
- [ ] Export or manually capture FAASTeam past events for February 2025
- [ ] Export or manually capture FAASTeam past events for March 2025
- [ ] Export or manually capture FAASTeam past events for April 2025
- [ ] Export or manually capture FAASTeam past events for May 2025
- [ ] Export or manually capture FAASTeam past events for June 2025
- [ ] Export or manually capture FAASTeam past events for July 2025
- [ ] Export or manually capture FAASTeam past events for August 2025
- [ ] Export or manually capture FAASTeam past events for September 2025
- [ ] Export or manually capture FAASTeam past events for October 2025
- [ ] Export or manually capture FAASTeam past events for November 2025
- [ ] Export or manually capture FAASTeam past events for December 2025
- [ ] Export or manually capture FAASTeam past events for January 2026
- [ ] Export or manually capture FAASTeam past events for February 2026

Operational note:
- FAASTeam’s public past-events search is limited to the past 15 months, which aligns well with this supplemental window.

## Aggregate-Only Integration Rules
- Keep cross-source integration at month, airport, route, carrier group, operator group, state, or region
- Do not join public BTS flight legs directly to ASRS narratives or NTSB investigations
- Do not imply access to FOQA, ASAP, internal SMS, or other confidential airline systems
- Keep source-native supplemental dashboards clearly separate from integrated cross-source dashboards when source coverage differs

## Rebuild Order After Real Files Are Placed
1. Place verified raw public files into the correct `data/raw` subfolders
2. Rebuild the main trusted layer:
   - `python3 -m src.transform.build_trusted_layer`
3. Rebuild any standalone trusted adapters if source-specific validation needs to be inspected separately
4. Rebuild integrated analytics marts:
   - `python3 -m src.features.build_analytics_marts`
5. Validate that the analytics outputs reflect the intended date windows before opening Tableau
6. Rebuild Dashboard 1 and the supporting Tableau dashboards from the refreshed analytics files

## Interview-Defensible Framing
- Integrated views should be described as `public-data-based`, `aggregate-only`, and `proxy-driven`
- Source-native supplemental views should be described as broader context windows that are not perfectly cross-source comparable month by month
- If December 2025 BTS On-Time data remain unavailable, say so explicitly and cap integrated public operational views at the latest official BTS month
