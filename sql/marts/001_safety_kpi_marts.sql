-- Analytics-facing marts for Tableau and reporting.

CREATE VIEW mart_monthly_safety_summary AS
SELECT
    EXTRACT(YEAR FROM event_date) AS event_year,
    EXTRACT(MONTH FROM event_date) AS event_month,
    source_system,
    COUNT(*) AS event_count,
    AVG(severity_score) AS avg_severity_score
FROM trusted_safety_events
GROUP BY 1, 2, 3;


CREATE VIEW mart_fatigue_proxy_signals AS
SELECT
    EXTRACT(YEAR FROM event_date) AS event_year,
    EXTRACT(MONTH FROM event_date) AS event_month,
    SUM(CASE WHEN LOWER(source_system) LIKE '%asrs%' THEN 1 ELSE 0 END) AS fatigue_proxy_event_count,
    AVG(severity_score) AS avg_proxy_severity_score
FROM trusted_safety_events
GROUP BY 1, 2;
