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
    stored_provenance TEXT;
    stored_composition_state TEXT;
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

    SELECT job_id, candidate_set_fingerprint, candidate_ids,
           delivered_answer_provenance, composition_state
    INTO stored_job_id, stored_fingerprint, stored_candidate_ids,
         stored_provenance, stored_composition_state
    FROM gold_star_adjudication_jobs
    WHERE request_id = p_request_id
      AND attempt_ordinal = p_attempt_ordinal
      AND adjudication_kind = 'gold_star_candidate';

    IF stored_fingerprint IS DISTINCT FROM p_candidate_set_fingerprint
       OR stored_candidate_ids IS DISTINCT FROM p_candidate_ids
       OR stored_provenance IS DISTINCT FROM p_delivered_answer_provenance
       OR stored_composition_state IS DISTINCT FROM p_composition_state THEN
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

CREATE OR REPLACE FUNCTION complete_gold_star_adjudication_job(
    p_job_id UUID,
    p_worker_id UUID,
    p_result_id UUID,
    p_result_version TEXT,
    p_disposition TEXT,
    p_selected_candidate_ids TEXT[] DEFAULT '{}',
    p_rejected_candidate_ids TEXT[] DEFAULT '{}',
    p_abstained_candidate_ids TEXT[] DEFAULT '{}',
    p_reason_codes JSONB DEFAULT '{}'::jsonb,
    p_applicability_conditions TEXT[] DEFAULT '{}',
    p_abstention_boundaries TEXT[] DEFAULT '{}',
    p_evidence_refs TEXT[] DEFAULT '{}',
    p_insufficient_evidence BOOLEAN DEFAULT FALSE,
    p_adjudicator_provider TEXT DEFAULT 'unknown',
    p_adjudicator_model TEXT DEFAULT 'unknown'
)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $complete$
DECLARE
    current_job gold_star_adjudication_jobs%ROWTYPE;
BEGIN
    SELECT *
    INTO current_job
    FROM gold_star_adjudication_jobs
    WHERE job_id = p_job_id
    FOR UPDATE;

    IF NOT FOUND
       OR current_job.adjudication_state <> 'claimed'
       OR current_job.worker_id IS DISTINCT FROM p_worker_id THEN
        RAISE EXCEPTION 'job_lease_not_owned';
    END IF;

    IF p_disposition IS NULL OR p_disposition NOT IN (
        'adjudicated_selected', 'adjudicated_rejected',
        'abstained_insufficient_evidence', 'human_review_required'
    ) THEN
        RAISE EXCEPTION 'invalid_adjudication_disposition';
    END IF;

    IF COALESCE(p_selected_candidate_ids, '{}') && COALESCE(p_rejected_candidate_ids, '{}')
       OR COALESCE(p_selected_candidate_ids, '{}') && COALESCE(p_abstained_candidate_ids, '{}')
       OR COALESCE(p_rejected_candidate_ids, '{}') && COALESCE(p_abstained_candidate_ids, '{}') THEN
        RAISE EXCEPTION 'candidate_dispositions_overlap';
    END IF;

    IF NOT COALESCE(p_selected_candidate_ids, '{}') <@ current_job.candidate_ids
       OR NOT COALESCE(p_rejected_candidate_ids, '{}') <@ current_job.candidate_ids
       OR NOT COALESCE(p_abstained_candidate_ids, '{}') <@ current_job.candidate_ids THEN
        RAISE EXCEPTION 'adjudication_candidate_not_in_job';
    END IF;

    IF p_disposition = 'adjudicated_selected'
       AND cardinality(COALESCE(p_selected_candidate_ids, '{}')) = 0 THEN
        RAISE EXCEPTION 'selected_disposition_requires_candidate';
    END IF;
    IF p_disposition = 'adjudicated_rejected'
       AND cardinality(COALESCE(p_rejected_candidate_ids, '{}')) = 0 THEN
        RAISE EXCEPTION 'rejected_disposition_requires_candidate';
    END IF;
    IF p_disposition = 'abstained_insufficient_evidence'
       AND (
           NOT p_insufficient_evidence
           OR cardinality(COALESCE(p_abstained_candidate_ids, '{}')) = 0
       ) THEN
        RAISE EXCEPTION 'abstention_requires_insufficient_evidence';
    END IF;

    INSERT INTO gold_star_adjudication_results (
        result_id, job_id, result_version, selected_candidate_ids,
        rejected_candidate_ids, abstained_candidate_ids, reason_codes,
        applicability_conditions, abstention_boundaries, evidence_refs,
        insufficient_evidence, adjudicator_provider, adjudicator_model,
        adjudicated_at
    ) VALUES (
        p_result_id, p_job_id, p_result_version,
        COALESCE(p_selected_candidate_ids, '{}'),
        COALESCE(p_rejected_candidate_ids, '{}'),
        COALESCE(p_abstained_candidate_ids, '{}'),
        COALESCE(p_reason_codes, '{}'::jsonb),
        COALESCE(p_applicability_conditions, '{}'),
        COALESCE(p_abstention_boundaries, '{}'),
        COALESCE(p_evidence_refs, '{}'),
        COALESCE(p_insufficient_evidence, FALSE),
        p_adjudicator_provider, p_adjudicator_model, now()
    );

    UPDATE gold_star_adjudication_jobs
    SET adjudication_state = p_disposition,
        claimed_at = NULL,
        lease_expires_at = NULL,
        worker_id = NULL,
        completed_at = now(),
        updated_at = now(),
        last_error_class = NULL
    WHERE job_id = p_job_id;

    INSERT INTO gold_star_adjudication_events (
        event_id, job_id, previous_state, new_state,
        reason_code, worker_token, occurred_at
    ) VALUES (
        gen_random_uuid(), p_job_id, 'claimed', p_disposition,
        p_disposition, p_worker_id, now()
    );

    RETURN TRUE;
END;
$complete$;

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
