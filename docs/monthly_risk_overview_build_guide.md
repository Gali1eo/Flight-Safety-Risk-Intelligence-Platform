# Monthly Risk Overview Build Guide

## Purpose
This is the primary showcase dashboard for the Flight Safety Risk Intelligence Platform. It should demonstrate that public operational data, public safety-reporting data, public investigation data, and synthetic safety-culture data can be integrated responsibly at a monthly airport level without overstating what the data can prove.

## Data Source
- Primary file: `data/analytics/monthly_risk_overview.csv`
- Supporting documentation: `docs/tableau_data_dictionary.md`
- Strategic framing: `docs/tableau_dashboard_plan.md`

## Recommended Tableau Build Sequence

### 1. Connect and Validate The Data Source
- Connect Tableau to `monthly_risk_overview.csv`
- Confirm `report_month` is treated consistently; convert it into a date field for continuous month views
- Validate that the following fields are present:
  - `report_month`
  - `airport`
  - `region`
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
  - `data_basis`

### 2. Create Core Tableau Calculated Fields
Recommended calculations:

```text
Report Month Date
DATEPARSE("yyyy-MM", [report_month])
```

```text
Operational Disruption Rate
IF ZN([operational_flight_legs]) = 0 THEN NULL
ELSE (ZN([cancelled_flights]) + ZN([diverted_flights])) / ZN([operational_flight_legs])
END
```

```text
Fatigue Report Share
IF ZN([asrs_report_count]) = 0 THEN NULL
ELSE ZN([fatigue_related_report_count]) / ZN([asrs_report_count])
END
```

```text
Serious Investigation Share
IF ZN([ntsb_investigation_count]) = 0 THEN NULL
ELSE ZN([serious_or_higher_investigation_count]) / ZN([ntsb_investigation_count])
END
```

```text
Training Completion Percent
ZN([avg_training_completion_rate]) * 100
```

```text
Fatigue Training Completion Percent
ZN([fatigue_training_completion_rate]) * 100
```

### 3. Build Worksheets In This Order

#### Worksheet A: KPI Header
Goal:
Create a clean executive-style summary row for the dashboard.

Recommended KPI tiles:
- Operational Flight Legs
- Operational Disruption Rate
- ASRS Report Count
- Fatigue Report Share
- NTSB Investigation Count
- Serious Investigation Share
- Training Completion Percent

#### Worksheet B: Monthly Trend Story
Goal:
Show how operational disruption and safety-report activity move over time.

Suggested view:
- Continuous month line chart
- Lines for:
  - `operational_flight_legs`
  - `asrs_report_count`
  - `ntsb_investigation_count`

Design note:
- If the scales feel too different, use a dual-axis view only if the labeling stays very clear.

#### Worksheet C: Airport Risk Heatmap
Goal:
Show where public-data-based proxy signals cluster by airport and month.

Suggested view:
- Heatmap or highlight table
- Columns: `report_month`
- Rows: `airport`
- Color options:
  - `Operational Disruption Rate`
  - `Fatigue Report Share`
  - `Serious Investigation Share`

#### Worksheet D: Airport Comparison Scatter
Goal:
Create an interview-friendly “so what” view that compares operational pressure and voluntary reporting patterns.

Suggested view:
- Scatter plot
- X-axis: `avg_departure_delay_minutes`
- Y-axis: `fatigue_related_report_count`
- Size: `ntsb_investigation_count`
- Color: `region`
- Label: `airport`

#### Worksheet E: Synthetic Culture Context Table
Goal:
Keep the synthetic layer visible but clearly separated as a demonstration-only context source.

Suggested view:
- Text table or compact bar table
- Rows: `airport`
- Measures:
  - `Training Completion Percent`
  - `avg_safety_engagement_score`
  - `Fatigue Training Completion Percent`
  - `synthetic_elevated_risk_count`

### 4. Assemble The Dashboard
Recommended layout:
- Top row: Title + proxy disclaimer + KPI header
- Middle row: Monthly trend story on the left, airport risk heatmap on the right
- Bottom row: Scatter plot on the left, synthetic culture context table on the right

Recommended title:
- `Monthly Risk Overview (Public-Data-Based, Proxy-Driven)`

Recommended subtitle:
- `Integrates public BTS operations, public NASA ASRS reports, public NTSB investigations, and synthetic safety-culture indicators at monthly airport level.`

### 5. Add Filters
Recommended dashboard filters:
- Report Month
- Region
- Airport

Keep filters global across worksheets where practical.

### 6. Add Tooltip and Caption Language
Use tooltip language like:
- `Public operational proxy`
- `Voluntary safety-report proxy`
- `External investigation context`
- `Synthetic safety-culture indicator`

Recommended footer note:
- `This dashboard uses public BTS, ASRS, and NTSB data plus synthetic safety-culture data. It does not use airline-internal SMS, FOQA, or ASAP data. Cross-source relationships are aggregate and proxy-driven.`

## Interview Narrative
Use this dashboard to tell a simple sequence:
1. Start with operational context using BTS delays, cancellations, and diversions.
2. Show where voluntary ASRS safety-report volume and fatigue-related signals increase.
3. Add NTSB investigations as external severity context, not as direct matches.
4. Use synthetic culture indicators carefully to demonstrate how an internal context layer could be modeled without claiming real internal access.

## What To Avoid
- Do not imply event-level joins across BTS, ASRS, and NTSB.
- Do not describe synthetic culture metrics as real airline data.
- Do not describe BTS as FOQA or ASRS as ASAP.
- Do not overstate low-count airports or months.
