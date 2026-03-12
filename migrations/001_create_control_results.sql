-- Create control_results table for storing control evaluation run results.
-- Run this against your database if the table does not exist (e.g. no Alembic).

CREATE TABLE IF NOT EXISTS control_results (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    control_id UUID NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
    run_at TIMESTAMP(0) NOT NULL,
    result VARCHAR(50) NOT NULL,
    details JSONB,
    evidence_ids JSONB,
    created_at TIMESTAMP(0)
);

CREATE INDEX IF NOT EXISTS control_results_organization_control_run_index
    ON control_results (organization_id, control_id, run_at);
