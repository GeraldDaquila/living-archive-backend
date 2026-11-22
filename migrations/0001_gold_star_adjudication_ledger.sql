-- Gold Star durable adjudication ledger, migration 0001.
-- Stores bounded operational metadata only. Never store visitor questions, answers,
-- identities, raw provider prompts/responses, credentials, or content hashes.
BEGIN;

CREATE TABLE IF NOT EXISTS gold_star_adjudication_jobs (
    job_id UUID PRIMARY KEY,
    request_id CHAR(32) NOT NULL
        CHECK (request_id ~ '^[0-9a-f]{32}$'),
    attempt_ordinal SMALLINT NOT NULL CHECK (attempt_ordinal BETWEEN 1 AND 32),
    adjudication_kind TEXT NOT NULL DEFAULT 'gold_star_candidate'
        CHECK (adjudication_kind = 'gold_star_candidate'),
    candidate_set_fingerprint CHAR(64) NOT NULL
        CHECK (candidate_set_fingerprint ~ '^[0-9a-f]{64}$'),
    candidate_ids TEXT[] NOT NULL
        CHECK (cardinality(candidate_ids) BETWEEN 1 AND 4),
    delivered_answer_provenance TEXT NOT NULL
        CHECK (delivered_answer_provenance IN (
            'provider_composition', 'deterministic_recovery',
            'registered_recovery', 'unknown'
        )),
    composition_state TEXT NOT NULL
        CHECK (composition_state IN (
            'provider_candidate_delivered', 'deterministic_or_unresolved_replacement',
            'unknown'
        )),
    adjudication_state TEXT NOT NULL
        CHECK (adjudication_state IN (
            'not_eligible', 'queued', 'claimed', 'budget_skipped',
            'provider_unavailable', 'adjudicated_selected',
            'adjudicated_rejected', 'abstained_insufficient_evidence',
            'retry_exhausted', 'human_review_required'
        )),
    attempt_count SMALLINT NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 3),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    lease_expires_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    worker_id UUID,
    provider_name TEXT CHECK (provider_name IS NULL OR length(provider_name) <= 80),
    model_name TEXT CHECK (model_name IS NULL OR length(model_name) <= 120),
    last_error_class TEXT CHECK (
        last_error_class IS NULL OR last_error_class IN (
            'timeout', 'connection_error', 'rate_limited',
            'provider_unavailable', 'invalid_response', 'internal_error'
        )
    ),
    UNIQUE (request_id, attempt_ordinal, adjudication_kind),
    CHECK (
        (adjudication_state = 'claimed'
            AND claimed_at IS NOT NULL
            AND lease_expires_at IS NOT NULL
            AND worker_id IS NOT NULL)
        OR
        (adjudication_state <> 'claimed'
            AND claimed_at IS NULL
            AND lease_expires_at IS NULL
            AND worker_id IS NULL)
    ),
    CHECK (
        (adjudication_state IN (
            'adjudicated_selected', 'adjudicated_rejected',
            'abstained_insufficient_evidence', 'retry_exhausted',
            'human_review_required', 'budget_skipped',
            'provider_unavailable', 'not_eligible'
        )) = (completed_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_gold_star_jobs_ready
    ON gold_star_adjudication_jobs (available_at, created_at_placeholder)
    WHERE adjudication_state = 'queued';

-- The created_at ordering is represented by job_id insertion order in the first
-- schema version; avoid an unneeded extra timestamp column or provider-side sort.
DROP INDEX IF EXISTS idx_gold_star_jobs_ready;
CREATE INDEX idx_gold_star_jobs_ready
    ON gold_star_adjudication_jobs (available_at, job_id)
    WHERE adjudication_state = 'queued';

CREATE INDEX IF NOT EXISTS idx_gold_star_jobs_expired_lease
    ON gold_star_adjudication_jobs (lease_expires_at)
    WHERE adjudication_state = 'claimed';

CREATE TABLE IF NOT EXISTS gold_star_adjudication_results (
    result_id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES gold_star_adjudication_jobs(job_id),
    result_version TEXT NOT NULL CHECK (length(result_version) BETWEEN 1 AND 40),
    selected_candidate_ids TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(selected_candidate_ids) <= 4),
    rejected_candidate_ids TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(rejected_candidate_ids) <= 4),
    abstained_candidate_ids TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(abstained_candidate_ids) <= 4),
    reason_codes JSONB NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(reason_codes) = 'object'),
    applicability_conditions TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(applicability_conditions) <= 8),
    abstention_boundaries TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(abstention_boundaries) <= 8),
    evidence_refs TEXT[] NOT NULL DEFAULT '{}'
        CHECK (cardinality(evidence_refs) <= 16),
    insufficient_evidence BOOLEAN NOT NULL DEFAULT FALSE,
    adjudicator_provider TEXT NOT NULL CHECK (length(adjudicator_provider) <= 80),
    adjudicator_model TEXT NOT NULL CHECK (length(adjudicator_model) <= 120),
    adjudicated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (job_id, result_version)
);

CREATE TABLE IF NOT EXISTS provider_capacity_reservations (
    reservation_id UUID PRIMARY KEY,
    operation_class TEXT NOT NULL CHECK (
        operation_class IN ('visitor_response', 'gold_star_adjudication')
    ),
    estimated_tokens INTEGER NOT NULL CHECK (estimated_tokens BETWEEN 1 AND 10000),
    reservation_state TEXT NOT NULL CHECK (
        reservation_state IN ('reserved', 'consumed', 'released', 'expired')
    ),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_provider_reservations_active
    ON provider_capacity_reservations (operation_class, expires_at)
    WHERE reservation_state = 'reserved';

CREATE TABLE IF NOT EXISTS gold_star_adjudication_events (
    event_id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES gold_star_adjudication_jobs(job_id),
    previous_state TEXT,
    new_state TEXT NOT NULL,
    reason_code TEXT NOT NULL CHECK (length(reason_code) BETWEEN 1 AND 80),
    worker_token UUID,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (previous_state IS NULL OR length(previous_state) <= 40),
    CHECK (length(new_state) <= 40)
);

CREATE INDEX IF NOT EXISTS idx_gold_star_events_job_time
    ON gold_star_adjudication_events (job_id, occurred_at);

-- Results and events are append-only. Mutations must be represented by new rows.
CREATE OR REPLACE FUNCTION gold_star_ledger_reject_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'gold_star_ledger_append_only';
END;
$$;

DROP TRIGGER IF EXISTS gold_star_results_append_only ON gold_star_adjudication_results;
CREATE TRIGGER gold_star_results_append_only
    BEFORE UPDATE OR DELETE ON gold_star_adjudication_results
    FOR EACH ROW EXECUTE FUNCTION gold_star_ledger_reject_mutation();

DROP TRIGGER IF EXISTS gold_star_events_append_only ON gold_star_adjudication_events;
CREATE TRIGGER gold_star_events_append_only
    BEFORE UPDATE OR DELETE ON gold_star_adjudication_events
    FOR EACH ROW EXECUTE FUNCTION gold_star_ledger_reject_mutation();

COMMIT;
