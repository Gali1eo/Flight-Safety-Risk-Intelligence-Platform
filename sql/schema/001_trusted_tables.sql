-- Trusted-layer table definitions for public and synthetic aviation safety proxies.

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

CREATE MULTISET TABLE trusted_training_safety_culture (
    employee_period_key VARCHAR(64) NOT NULL,
    period_start_date DATE,
    training_completion_rate DECIMAL(8, 4),
    safety_engagement_score DECIMAL(8, 4),
    fatigue_training_flag BYTEINT,
    ingest_timestamp TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP
)
PRIMARY INDEX (employee_period_key);
