-- Analytics-facing marts for Tableau and reporting.

CREATE VIEW mart_monthly_risk_overview AS
SELECT
    b.report_month,
    b.origin_airport AS airport,
    CASE
        WHEN b.origin_airport IN ('ATL') THEN 'Southeast'
        WHEN b.origin_airport IN ('MSP', 'DTW') THEN 'Midwest'
        WHEN b.origin_airport IN ('JFK', 'BOS') THEN 'Northeast'
        WHEN b.origin_airport IN ('SEA', 'LAX', 'SLC') THEN 'West'
        WHEN b.origin_airport IN ('DAL', 'HOU') THEN 'South'
        ELSE 'Unknown'
    END AS region,
    COUNT(*) AS operational_flight_legs,
    SUM(b.cancelled_flag) AS cancelled_flights,
    SUM(b.diverted_flag) AS diverted_flights,
    AVG(b.departure_delay_minutes) AS avg_departure_delay_minutes,
    AVG(b.arrival_delay_minutes) AS avg_arrival_delay_minutes,
    COUNT(DISTINCT a.report_id) AS asrs_report_count,
    SUM(CASE WHEN LOWER(a.human_factors) LIKE '%fatigue%' THEN 1 ELSE 0 END) AS fatigue_related_report_count,
    COUNT(DISTINCT n.ntsb_event_id) AS ntsb_investigation_count,
    SUM(CASE WHEN n.severity_normalized IN ('serious_injury', 'fatal_injury') THEN 1 ELSE 0 END) AS serious_or_higher_investigation_count,
    AVG(s.training_completion_rate) AS avg_training_completion_rate,
    AVG(s.safety_engagement_score) AS avg_safety_engagement_score,
    AVG(s.fatigue_training_flag) AS fatigue_training_completion_rate,
    SUM(CASE WHEN s.severity_score > 0 THEN 1 ELSE 0 END) AS synthetic_elevated_risk_count
FROM (
    SELECT
        SUBSTR(CAST(flight_date AS VARCHAR(10)), 1, 7) AS report_month,
        origin_airport,
        departure_delay_minutes,
        arrival_delay_minutes,
        cancelled_flag,
        diverted_flag
    FROM trusted_bts_on_time_operations
) b
LEFT JOIN trusted_nasa_asrs_reports a
    ON SUBSTR(CAST(a.event_date AS VARCHAR(10)), 1, 7) = b.report_month
    AND a.location = b.origin_airport
LEFT JOIN trusted_ntsb_aviation_investigations n
    ON SUBSTR(CAST(n.event_date AS VARCHAR(10)), 1, 7) = b.report_month
    AND n.airport_code = b.origin_airport
LEFT JOIN trusted_safety_events s
    ON SUBSTR(CAST(s.event_date AS VARCHAR(10)), 1, 7) = b.report_month
    AND s.base_location = b.origin_airport
GROUP BY 1, 2, 3;


CREATE VIEW mart_operational_disruption_summary AS
SELECT
    SUBSTR(CAST(flight_date AS VARCHAR(10)), 1, 7) AS report_month,
    carrier,
    origin_airport,
    destination_airport,
    route,
    COUNT(*) AS flight_leg_count,
    SUM(cancelled_flag) AS cancelled_flight_count,
    SUM(diverted_flag) AS diverted_flight_count,
    AVG(departure_delay_minutes) AS avg_departure_delay_minutes,
    AVG(arrival_delay_minutes) AS avg_arrival_delay_minutes
FROM trusted_bts_on_time_operations
GROUP BY 1, 2, 3, 4, 5;


CREATE VIEW mart_investigation_trends AS
SELECT
    SUBSTR(CAST(event_date AS VARCHAR(10)), 1, 7) AS report_month,
    airport_code AS airport,
    operator_name AS operator_group,
    investigation_category,
    severity_normalized,
    COUNT(*) AS investigation_count
FROM trusted_ntsb_aviation_investigations
GROUP BY 1, 2, 3, 4, 5;
