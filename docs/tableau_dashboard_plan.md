# Tableau Dashboard Plan

## Dashboard 1: Monthly Risk Overview
Goal:
Serve as the primary showcase dashboard for interviews by telling a clear story about how public operational disruption, voluntary safety reporting, external investigations, and synthetic culture indicators can be aligned at a truthful monthly airport level.

Build sequence:
- Connect `monthly_risk_overview.csv`
- Build KPI header first
- Build monthly trend story second
- Build airport heatmap third
- Build airport comparison scatter fourth
- Add synthetic culture context table last
- See `docs/monthly_risk_overview_build_guide.md` for the detailed worksheet-by-worksheet sequence

Primary KPIs:
- Operational Flight Legs
- Cancelled Flights
- Diverted Flights
- ASRS Report Count
- Fatigue Related Report Count
- NTSB Investigation Count
- Serious Or Higher Investigation Count
- Average Training Completion Rate
- Average Safety Engagement Score

Suggested chart types:
- KPI tiles for the headline metrics
- Dual-axis monthly line or area chart for operational volume versus ASRS report volume
- Airport heatmap by region and month
- Bubble or scatter plot comparing delay, fatigue reports, and investigation volume
- Highlight table for synthetic culture indicators by airport

Filters:
- Report Month
- Region
- Airport

Drill-down path:
Month to Region to Airport to supporting route or source-specific dashboard.

Proxy caveats:
- This dashboard combines public proxies and synthetic data at monthly airport level only.
- It should never imply direct event-level linkage or internal airline system access.
- Synthetic culture metrics must be visibly labeled as synthetic demonstration data.

## Dashboard 2: Fatigue Theme Trends
Goal:
Show how public voluntary ASRS reporting themes shift by month, airport, and carrier proxy, with special focus on fatigue-related reporting patterns.

Primary KPIs:
- Report Count
- Fatigue Related Report Count
- Unique Anomaly Count

Suggested chart types:
- Stacked bar chart by human-factor theme
- Monthly trend line for fatigue-related reports
- Airport or region map
- Carrier comparison bar chart

Filters:
- Report Month
- Airport
- Region
- Carrier
- Human Factor Theme

Drill-down path:
Month to Region to Airport to Carrier to Human Factor Theme.

Proxy caveats:
- ASRS is a public voluntary-reporting proxy and not ASAP.
- Theme volume reflects reporting behavior, not complete event capture.
- Carrier groupings are simplified for storytelling.

## Dashboard 3: Investigation Trends
Goal:
Summarize public investigation volume, normalized severity, and occurrence categories for contextual safety storytelling.

Primary KPIs:
- Investigation Count
- Serious Or Higher Count
- Serious Investigation Share

Suggested chart types:
- Severity trend line by month
- Stacked bars for investigation categories
- Airport or region heatmap
- Operator group comparison bars

Filters:
- Report Month
- Airport
- Region
- Operator Group
- Investigation Category
- Severity Normalized

Drill-down path:
Month to Region to Airport to Operator Group to Investigation Category.

Proxy caveats:
- NTSB is an external investigation source, not an internal airline safety monitoring system.
- Investigation timing may lag the actual event.
- Lower-volume slices should be interpreted cautiously.

## Dashboard 4: Operational Disruption Summary
Goal:
Show public route- and carrier-level disruption patterns that can be used as operational context for broader safety storytelling.

Primary KPIs:
- Flight Leg Count
- Cancelled Flight Count
- Diverted Flight Count
- Cancellation Rate
- Diversion Rate
- Average Departure Delay Minutes
- Average Arrival Delay Minutes

Suggested chart types:
- Route performance table
- Carrier comparison bars
- Delay trend line by month
- Origin-destination heatmap

Filters:
- Report Month
- Carrier
- Origin Airport
- Destination Airport
- Route
- Region

Drill-down path:
Month to Carrier to Origin Airport to Route.

Proxy caveats:
- BTS operations data is a public operational proxy, not FOQA.
- Delays and disruptions should be framed as context, not direct safety outcomes.

## Dashboard 5: Safety Promotion Summary
Goal:
Show public outreach coverage, topic mix, and audience targeting using FAASTeam event data as a safety-promotion proxy.

Primary KPIs:
- Event Count
- Distinct Topic Count
- Distinct Audience Type Count

Suggested chart types:
- Topic mix bar chart
- Region or state map
- Monthly outreach trend line
- Audience type stacked bars

Filters:
- Report Month
- State
- Region
- Topic
- Audience Type

Drill-down path:
Month to Region to State to Topic to Audience Type.

Proxy caveats:
- FAASTeam events are public outreach records, not internal airline training completions.
- Geographic alignment to airport operations is approximate.

## Recommended Dashboard Build Order
1. Monthly Risk Overview
2. Operational Disruption Summary
3. Fatigue Theme Trends
4. Investigation Trends
5. Safety Promotion Summary

## Presentation Guidance
- Lead interviews with Monthly Risk Overview because it best demonstrates integration, restraint, and business storytelling.
- Use the other four dashboards as supporting deep dives into each proxy source.
- Keep dashboard subtitles explicit about public-data and proxy-based design.
