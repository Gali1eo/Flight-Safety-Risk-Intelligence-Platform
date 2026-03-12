-- Trusted and analytics-layer table definitions for public and synthetic aviation safety proxies.

CREATE MULTISET TABLE trusted_safety_events (
    event_id VARCHAR(64) NOT NULL,
    event_date DATE,
    source_system VARCHAR(64) NOT NULL,
    event_category VARCHAR(128),
    severity_score DECIMAL(8, 2),
    location_code VARCHAR(16),
    report_text VARCHAR(5000),
    ingest_timestamp TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
)
PRIMARY INDEX (event_id);

CREATE MULTISET TABLE trusted_nasa_asrs_reports (
    report_id VARCHAR(64) NOT NULL,
    event_date DATE,
    location VARCHAR(32),
    aircraft_operator VARCHAR(128),
    anomaly VARCHAR(128),
    human_factors VARCHAR(128),
    narrative VARCHAR(5000),
    source_system VARCHAR(64),
    raw_file_name VARCHAR(255)
)
PRIMARY INDEX (report_id);

CREATE MULTISET TABLE trusted_ntsb_aviation_investigations (
    ntsb_event_id VARCHAR(64) NOT NULL,
    event_date DATE,
    airport_code VARCHAR(16),
    operator_name VARCHAR(128),
    injury_severity VARCHAR(64),
    event_type VARCHAR(128),
    aircraft_damage VARCHAR(64),
    severity_normalized VARCHAR(64),
    investigation_category VARCHAR(64),
    source_system VARCHAR(64)
)
PRIMARY INDEX (ntsb_event_id);

CREATE MULTISET TABLE trusted_bts_on_time_operations (
    flight_date DATE,
    reporting_airline VARCHAR(16),
    flight_number VARCHAR(16),
    origin VARCHAR(16),
    dest VARCHAR(16),
    route VARCHAR(32),
    departure_delay_minutes DECIMAL(10, 2),
    arrival_delay_minutes DECIMAL(10, 2),
    cancelled_flag BYTEINT,
    diverted_flag BYTEINT,
    operational_status VARCHAR(32),
    raw_file_name VARCHAR(255)
)
PRIMARY INDEX (flight_date, reporting_airline, flight_number, origin, dest);

CREATE MULTISET TABLE mart_monthly_risk_overview (
    report_month VARCHAR(7),
    airport VARCHAR(16),
    region VARCHAR(32),
    operational_flight_legs INTEGER,
    cancelled_flights INTEGER,
    diverted_flights INTEGER,
    avg_departure_delay_minutes DECIMAL(10, 2),
    avg_arrival_delay_minutes DECIMAL(10, 2),
    asrs_report_count INTEGER,
    fatigue_related_report_count INTEGER,
    ntsb_investigation_count INTEGER,
    serious_or_higher_investigation_count INTEGER,
    avg_training_completion_rate DECIMAL(10, 4),
    avg_safety_engagement_score DECIMAL(10, 4),
    fatigue_training_completion_rate DECIMAL(10, 4),
    synthetic_elevated_risk_count INTEGER,
    data_basis VARCHAR(500)
)
PRIMARY INDEX (report_month, airport);

CREATE MULTISET TABLE mart_fatigue_theme_trends (
    report_month VARCHAR(7),
    airport VARCHAR(16),
    carrier VARCHAR(16),
    region VARCHAR(32),
    human_factor_theme VARCHAR(128),
    fatigue_related_flag BYTEINT,
    report_count INTEGER,
    unique_anomaly_count INTEGER,
    data_basis VARCHAR(500)
)
PRIMARY INDEX (report_month, airport, carrier);
