-- Gold Star bounded queue operations, migration 0002.
-- Claims are transactional and concurrency-safe. Visitor delivery does not call these functions.
BEGIN;

CREATE OR REPLACE FUNCTION enqueue_gold_star_adjudication_job(
    p_job_id UUID,
    p_request_id CHAR(32),
    p_attempt_ordinal SMALLINT,
    p_candidate_set_fingerprint CHAR(64),
    p_candidate_ids TEXT[],
    p_delivered_answer_provenance TEXT,
    p_composition_state TEXT
)
RETURNS UUID
LANGUAGE plpgsql
AS $enqueue$
DECLARE
    stored_job_id UUID;
    stored_fingerprint CHAR(64);
    stored_candidate_ids TEXT[];
BEGIN
    IF p_job_id IS NULL THEN
        RAISE EXCEPTION 'job_id_required';
    END IF;

    INSERT INTO gold_star_adjudication_jobs (
        job_id, request_id, attempt_ordinal, candidate_set_fingerprint,
        candidate_ids, delivered_answer_provenance, composition_state,
        adjudication_state
    ) VALUES (
        p_job_id, p_request_id, p_attempt_ordinal, p_candidate_set_fingerprint,
        p_candidate_ids, p_delivered_answer_provenance, p_composition_state,
        'queued'
    )
    ON CONFLICT (request_id, attempt_ordinal, adjudication_kind) DO NOTHING
    RETURNING job_id INTO stored_job_id;

    IF FOUND THEN
        INSERT INTO gold_star_adjudication_events (
            event_id, job_id, previous_state, new_state,
            reason_code, occurred_at
        ) VALUES (
            gen_random_uuid(), stored_job_id, NULL, 'queued',
            'job_enqueued', now()
        );
        RETURN stored_job_id;
    END IF;

    SELECT job_id, candidate_set_fingerprint, candidate_ids
    INTO stored_job_id, stored_fingerprint, stored_candidate_ids
    FROM gold_star_adjudication_jobs
    WHERE request_id = p_request_id
      AND attempt_ordinal = p_attempt_ordinal
      AND adjudication_kind = 'gold_star_candidate';

    IF stored_fingerprint IS DISTINCT FROM p_candidate_set_fingerprint
       OR stored_candidate_ids IS DISTINCT FROM p_candidate_ids THEN
        RAISE EXCEPTION 'idempotency_key_payload_conflict';
    END IF;

    RETURN stored_job_id;
END;
$enqueue$;

CREATE OR REPLACE FUNCTION claim_gold_star_adjudication_jobs(
    p_worker_id UUID,
    p_limit INTEGER DEFAULT 1,
    p_lease_seconds INTEGER DEFAULT 120
)
RETURNS SETOF gold_star_adjudication_jobs
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_worker_id IS NULL THEN
        RAISE EXCEPTION 'worker_id_required';
    END IF;
    IF p_limit IS NULL OR p_limit < 1 OR p_limit > 8 THEN
        RAISE EXCEPTION 'claim_limit_out_of_range';
    END IF;
    IF p_lease_seconds IS NULL OR p_lease_seconds < 10 OR p_lease_seconds > 900 THEN
        RAISE EXCEPTION 'lease_seconds_out_of_range';
    END IF;

    RETURN QUERY
    WITH picked AS (
        SELECT job_id
        FROM gold_star_adjudication_jobs
        WHERE adjudication_state = 'queued'
          AND available_at <= now()
          AND attempt_count < 3
        ORDER BY available_at, created_at, job_id
        FOR UPDATE SKIP LOCKED
        LIMIT p_limit
    ),
    claimed AS (
        UPDATE gold_star_adjudication_jobs AS job
        SET adjudication_state = 'claimed',
            attempt_count = job.attempt_count + 1,
            claimed_at = now(),
            lease_expires_at = now() + make_interval(secs => p_lease_seconds),
            updated_at = now(),
            worker_id = p_worker_id
        FROM picked
        WHERE job.job_id = picked.job_id
        RETURNING job.*
    ),
    logged AS (
        INSERT INTO gold_star_adjudication_events (
            event_id, job_id, previous_state, new_state,
            reason_code, worker_token, occurred_at
        )
        SELECT gen_random_uuid(), job_id, 'queued', 'claimed',
               'worker_claimed', p_worker_id, now()
        FROM claimed
        RETURNING job_id
    )
    SELECT claimed.*
    FROM claimed
    JOIN logged USING (job_id);
END;
$$;

CREATE OR REPLACE FUNCTION recover_expired_gold_star_adjudication_leases()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    recovered_count INTEGER;
BEGIN
    WITH expired AS (
        SELECT job_id, worker_id
        FROM gold_star_adjudication_jobs
        WHERE adjudication_state = 'claimed'
          AND lease_expires_at <= now()
        ORDER BY lease_expires_at, job_id
        FOR UPDATE SKIP LOCKED
    ),
    reset AS (
        UPDATE gold_star_adjudication_jobs AS job
        SET adjudication_state = CASE
                WHEN job.attempt_count >= 3 THEN 'retry_exhausted'
                ELSE 'queued'
            END,
            available_at = CASE
                WHEN job.attempt_count >= 3 THEN job.available_at
                ELSE now() + make_interval(secs => 15 * job.attempt_count)
            END,
            claimed_at = NULL,
            lease_expires_at = NULL,
            worker_id = NULL,
            completed_at = CASE
                WHEN job.attempt_count >= 3 THEN now()
                ELSE NULL
            END,
            updated_at = now(),
            last_error_class = 'timeout'
        FROM expired
        WHERE job.job_id = expired.job_id
        RETURNING job.job_id, job.adjudication_state
    ),
    logged AS (
        INSERT INTO gold_star_adjudication_events (
            event_id, job_id, previous_state, new_state,
            reason_code, worker_token, occurred_at
        )
        SELECT gen_random_uuid(), reset.job_id, 'claimed',
               reset.adjudication_state,
               CASE WHEN reset.adjudication_state = 'queued'
                    THEN 'lease_expired_requeued'
                    ELSE 'lease_expired_retry_exhausted'
               END,
               expired.worker_id, now()
        FROM reset
        JOIN expired USING (job_id)
        RETURNING job_id
    )
    SELECT count(*)::INTEGER
    INTO recovered_count
    FROM logged;

    RETURN recovered_count;
END;
$$;

COMMIT;
