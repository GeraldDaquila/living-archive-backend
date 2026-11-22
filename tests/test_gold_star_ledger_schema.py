from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import errors


DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="TEST_DATABASE_URL is required")


@pytest.fixture(scope="session")
def database():
    assert DATABASE_URL
    with psycopg.connect(DATABASE_URL, autocommit=True) as connection:
        migration_dir = Path(__file__).resolve().parents[1] / "migrations"
        for migration_path in sorted(migration_dir.glob("*.sql")):
            connection.execute(migration_path.read_text(encoding="utf-8"), prepare=False)
        yield connection


def _insert_job(connection, *, state="queued", candidate_ids=None, request_id=None):
    job_id = uuid.uuid4()
    connection.execute(
        """
        INSERT INTO gold_star_adjudication_jobs (
            job_id, request_id, attempt_ordinal, candidate_set_fingerprint,
            candidate_ids, delivered_answer_provenance, composition_state,
            adjudication_state
        ) VALUES (%s, %s, 1, %s, %s, 'provider_composition',
                  'provider_candidate_delivered', %s)
        """,
        (
            job_id,
            request_id or uuid.uuid4().hex,
            "a" * 64,
            candidate_ids or ["lesson-a", "lesson-b"],
            state,
        ),
    )
    return job_id


def test_migration_creates_all_four_bounded_ledger_tables(database):
    rows = database.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = current_schema()
          AND table_name IN (
            'gold_star_adjudication_jobs',
            'gold_star_adjudication_results',
            'provider_capacity_reservations',
            'gold_star_adjudication_events'
          )
        """
    ).fetchall()
    assert {row[0] for row in rows} == {
        "gold_star_adjudication_jobs",
        "gold_star_adjudication_results",
        "provider_capacity_reservations",
        "gold_star_adjudication_events",
    }


def test_enqueue_idempotency_is_enforced_by_database(database):
    request_id = uuid.uuid4().hex
    _insert_job(database, request_id=request_id)
    with pytest.raises(errors.UniqueViolation):
        _insert_job(database, request_id=request_id)


def test_candidate_bound_is_enforced(database):
    with pytest.raises(errors.CheckViolation):
        _insert_job(database, candidate_ids=["a", "b", "c", "d", "e"])


def test_claimed_job_requires_complete_lease_metadata(database):
    with pytest.raises(errors.CheckViolation):
        _insert_job(database, state="claimed")


def test_completed_terminal_job_requires_completion_timestamp(database):
    with pytest.raises(errors.CheckViolation):
        _insert_job(database, state="adjudicated_rejected")


def test_result_records_are_append_only(database):
    job_id = _insert_job(database)
    result_id = uuid.uuid4()
    database.execute(
        """
        INSERT INTO gold_star_adjudication_results (
            result_id, job_id, result_version, selected_candidate_ids,
            adjudicator_provider, adjudicator_model
        ) VALUES (%s, %s, 'v1', ARRAY['lesson-a'], 'provider-a', 'model-a')
        """,
        (result_id, job_id),
    )
    with pytest.raises(errors.RaiseException, match="gold_star_ledger_append_only"):
        database.execute(
            "UPDATE gold_star_adjudication_results SET insufficient_evidence = TRUE WHERE result_id = %s",
            (result_id,),
        )


def test_event_records_are_append_only(database):
    job_id = _insert_job(database)
    event_id = uuid.uuid4()
    database.execute(
        """
        INSERT INTO gold_star_adjudication_events (
            event_id, job_id, previous_state, new_state, reason_code
        ) VALUES (%s, %s, NULL, 'queued', 'job_enqueued')
        """,
        (event_id, job_id),
    )
    with pytest.raises(errors.RaiseException, match="gold_star_ledger_append_only"):
        database.execute(
            "DELETE FROM gold_star_adjudication_events WHERE event_id = %s",
            (event_id,),
        )


def test_claim_function_claims_only_bounded_queued_jobs(database):
    _insert_job(database)
    worker_id = uuid.uuid4()
    rows = database.execute(
        "SELECT job_id, adjudication_state, attempt_count, worker_id "
        "FROM claim_gold_star_adjudication_jobs(%s, 1, 30)",
        (worker_id,),
    ).fetchall()
    assert len(rows) == 1
    assert rows[0][1] == "claimed"
    assert rows[0][2] == 1
    assert rows[0][3] == worker_id


def test_claim_function_rejects_unbounded_worker_parameters(database):
    with pytest.raises(errors.RaiseException, match="claim_limit_out_of_range"):
        database.execute(
            "SELECT * FROM claim_gold_star_adjudication_jobs(%s, 99, 30)",
            (uuid.uuid4(),),
        )
    with pytest.raises(errors.RaiseException, match="lease_seconds_out_of_range"):
        database.execute(
            "SELECT * FROM claim_gold_star_adjudication_jobs(%s, 1, 1)",
            (uuid.uuid4(),),
        )
    with pytest.raises(errors.RaiseException, match="claim_limit_out_of_range"):
        database.execute(
            "SELECT * FROM claim_gold_star_adjudication_jobs(%s, NULL, 30)",
            (uuid.uuid4(),),
        )


def test_two_concurrent_workers_never_claim_the_same_job(database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    _insert_job(database)
    _insert_job(database)
    barrier = Barrier(2)

    def claim(worker_id):
        with psycopg.connect(DATABASE_URL) as connection:
            barrier.wait(timeout=10)
            return connection.execute(
                "SELECT job_id FROM claim_gold_star_adjudication_jobs(%s, 1, 60)",
                (worker_id,),
            ).fetchone()[0]

    worker_ids = [uuid.uuid4(), uuid.uuid4()]
    with ThreadPoolExecutor(max_workers=2) as pool:
        claimed = list(pool.map(claim, worker_ids))
    assert len(set(claimed)) == 2


def test_expired_lease_is_requeued_and_event_is_recorded(database):
    job_id = _insert_job(database)
    worker_id = uuid.uuid4()
    database.execute(
        """
        UPDATE gold_star_adjudication_jobs
        SET adjudication_state = 'claimed', attempt_count = 1,
            claimed_at = now() - interval '2 minutes',
            lease_expires_at = now() - interval '1 minute',
            worker_id = %s
        WHERE job_id = %s
        """,
        (worker_id, job_id),
    )
    recovered = database.execute(
        "SELECT recover_expired_gold_star_adjudication_leases()"
    ).fetchone()[0]
    assert recovered == 1
    row = database.execute(
        "SELECT adjudication_state, claimed_at, lease_expires_at, worker_id, "
        "completed_at, last_error_class "
        "FROM gold_star_adjudication_jobs WHERE job_id = %s",
        (job_id,),
    ).fetchone()
    assert row == ("queued", None, None, None, None, "timeout")
    event = database.execute(
        "SELECT previous_state, new_state, reason_code, worker_token "
        "FROM gold_star_adjudication_events WHERE job_id = %s "
        "ORDER BY occurred_at DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    assert event == ("claimed", "queued", "lease_expired_requeued", worker_id)


def test_third_expired_lease_becomes_terminal_retry_exhausted(database):
    job_id = _insert_job(database)
    database.execute(
        """
        UPDATE gold_star_adjudication_jobs
        SET adjudication_state = 'claimed', attempt_count = 3,
            claimed_at = now() - interval '2 minutes',
            lease_expires_at = now() - interval '1 minute',
            worker_id = %s
        WHERE job_id = %s
        """,
        (uuid.uuid4(), job_id),
    )
    recovered = database.execute(
        "SELECT recover_expired_gold_star_adjudication_leases()"
    ).fetchone()[0]
    assert recovered == 1
    row = database.execute(
        "SELECT adjudication_state, completed_at, worker_id "
        "FROM gold_star_adjudication_jobs WHERE job_id = %s",
        (job_id,),
    ).fetchone()
    assert row[0] == "retry_exhausted"
    assert row[1] is not None
    assert row[2] is None



def _enqueue_job(connection, *, request_id=None, candidate_ids=None, fingerprint=None):
    return connection.execute(
        """
        SELECT enqueue_gold_star_adjudication_job(
            %s::uuid, %s::char(32), 1::smallint,
            %s::char(64), %s::text[],
            'provider_composition'::text, 'provider_candidate_delivered'::text
        )
        """,
        (
            uuid.uuid4(),
            request_id or uuid.uuid4().hex,
            fingerprint or "b" * 64,
            candidate_ids or ["lesson-x", "lesson-y"],
        ),
    ).fetchone()[0]


def test_enqueue_is_idempotent_and_records_one_event(database):
    request_id = uuid.uuid4().hex
    first = _enqueue_job(database, request_id=request_id)
    second = _enqueue_job(database, request_id=request_id)
    assert first == second
    count = database.execute(
        "SELECT count(*) FROM gold_star_adjudication_events "
        "WHERE job_id = %s AND reason_code = 'job_enqueued'",
        (first,),
    ).fetchone()[0]
    assert count == 1


def test_enqueue_rejects_reuse_of_idempotency_key_with_different_payload(database):
    request_id = uuid.uuid4().hex
    _enqueue_job(database, request_id=request_id)
    with pytest.raises(errors.RaiseException, match="idempotency_key_payload_conflict"):
        _enqueue_job(
            database,
            request_id=request_id,
            candidate_ids=["different-lesson"],
            fingerprint="c" * 64,
        )



def _mark_job_claimed(connection, job_id, worker_id):
    connection.execute(
        """
        UPDATE gold_star_adjudication_jobs
        SET adjudication_state = 'claimed', attempt_count = 1,
            claimed_at = now(), lease_expires_at = now() + interval '1 minute',
            worker_id = %s
        WHERE job_id = %s
        """,
        (worker_id, job_id),
    )


def test_completion_atomically_records_result_and_clears_lease(database):
    job_id = _insert_job(database)
    worker_id = uuid.uuid4()
    _mark_job_claimed(database, job_id, worker_id)
    result_id = uuid.uuid4()
    completed = database.execute(
        """
        SELECT complete_gold_star_adjudication_job(
            %s::uuid, %s::uuid, %s::uuid, 'v1'::text,
            'adjudicated_selected'::text,
            %s::text[], '{}'::text[], '{}'::text[], '{}'::jsonb,
            '{}'::text[], '{}'::text[], ARRAY['evidence-1']::text[],
            FALSE, 'test-provider'::text, 'test-model'::text
        )
        """,
        (job_id, worker_id, result_id, ["lesson-a"]),
    ).fetchone()[0]
    assert completed is True
    job = database.execute(
        "SELECT adjudication_state, completed_at, claimed_at, "
        "lease_expires_at, worker_id FROM gold_star_adjudication_jobs "
        "WHERE job_id = %s",
        (job_id,),
    ).fetchone()
    assert job[0] == "adjudicated_selected"
    assert job[1] is not None
    assert job[2:] == (None, None, None)
    result = database.execute(
        "SELECT selected_candidate_ids, evidence_refs, adjudicator_provider "
        "FROM gold_star_adjudication_results WHERE result_id = %s",
        (result_id,),
    ).fetchone()
    assert result == (["lesson-a"], ["evidence-1"], "test-provider")
    event = database.execute(
        "SELECT previous_state, new_state, reason_code "
        "FROM gold_star_adjudication_events WHERE job_id = %s "
        "ORDER BY occurred_at DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    assert event == ("claimed", "adjudicated_selected", "adjudicated_selected")


def test_completion_rejects_candidate_outside_claimed_job(database):
    job_id = _insert_job(database)
    worker_id = uuid.uuid4()
    _mark_job_claimed(database, job_id, worker_id)
    with pytest.raises(errors.RaiseException, match="adjudication_candidate_not_in_job"):
        database.execute(
            """
            SELECT complete_gold_star_adjudication_job(
                %s::uuid, %s::uuid, %s::uuid, 'v1'::text,
                'adjudicated_selected'::text,
                ARRAY['not-a-candidate']::text[], '{}'::text[], '{}'::text[],
                '{}'::jsonb, '{}'::text[], '{}'::text[], '{}'::text[],
                FALSE, 'test-provider'::text, 'test-model'::text
            )
            """,
            (job_id, worker_id, uuid.uuid4()),
        )
    state = database.execute(
        "SELECT adjudication_state FROM gold_star_adjudication_jobs WHERE job_id = %s",
        (job_id,),
    ).fetchone()[0]
    assert state == "claimed"


def test_completion_rejects_non_owner_and_duplicate_completion(database):
    job_id = _insert_job(database)
    worker_id = uuid.uuid4()
    _mark_job_claimed(database, job_id, worker_id)
    with pytest.raises(errors.RaiseException, match="job_lease_not_owned"):
        database.execute(
            """
            SELECT complete_gold_star_adjudication_job(
                %s::uuid, %s::uuid, %s::uuid, 'v1'::text,
                'adjudicated_rejected'::text,
                '{}'::text[], ARRAY['lesson-a']::text[], '{}'::text[],
                '{}'::jsonb, '{}'::text[], '{}'::text[], '{}'::text[],
                FALSE, 'test-provider'::text, 'test-model'::text
            )
            """,
            (job_id, uuid.uuid4(), uuid.uuid4()),
        )
    database.execute(
        """
        SELECT complete_gold_star_adjudication_job(
            %s::uuid, %s::uuid, %s::uuid, 'v1'::text,
            'adjudicated_rejected'::text,
            '{}'::text[], ARRAY['lesson-a']::text[], '{}'::text[],
            '{}'::jsonb, '{}'::text[], '{}'::text[], '{}'::text[],
            FALSE, 'test-provider'::text, 'test-model'::text
        )
        """,
        (job_id, worker_id, uuid.uuid4()),
    )
    with pytest.raises(errors.RaiseException, match="job_lease_not_owned"):
        database.execute(
            """
            SELECT complete_gold_star_adjudication_job(
                %s::uuid, %s::uuid, %s::uuid, 'v2'::text,
                'adjudicated_rejected'::text,
                '{}'::text[], ARRAY['lesson-a']::text[], '{}'::text[],
                '{}'::jsonb, '{}'::text[], '{}'::text[], '{}'::text[],
                FALSE, 'test-provider'::text, 'test-model'::text
            )
            """,
            (job_id, worker_id, uuid.uuid4()),
        )
