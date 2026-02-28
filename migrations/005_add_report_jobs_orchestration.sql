CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE report_requests
  ADD COLUMN IF NOT EXISTS request_hash VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_report_requests_request_hash
  ON report_requests(request_hash);

CREATE TABLE IF NOT EXISTS report_jobs (
    id BIGSERIAL PRIMARY KEY,
    report_request_id BIGINT NOT NULL REFERENCES report_requests(id) ON DELETE CASCADE,
    state VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
    current_stage VARCHAR(32) NOT NULL DEFAULT 'INGESTING',
    attempt INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    next_run_at TIMESTAMP NOT NULL DEFAULT NOW(),
    locked_by VARCHAR(128),
    locked_at TIMESTAMP,
    last_error_code VARCHAR(64),
    last_error_message TEXT,
    retryable BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_modified_at TIMESTAMP NOT NULL DEFAULT NOW(),
    public_id VARCHAR(36) NOT NULL DEFAULT gen_random_uuid()::text,
    CONSTRAINT uq_report_jobs_report_request UNIQUE (report_request_id)
);

CREATE INDEX IF NOT EXISTS idx_report_jobs_state_next_run
  ON report_jobs(state, next_run_at);

CREATE INDEX IF NOT EXISTS idx_report_jobs_locked_at
  ON report_jobs(locked_at);
