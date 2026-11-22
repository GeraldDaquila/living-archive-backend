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
        migration = (
            Path(__file__).resolve().parents[1]
            / "migrations"
            / "0001_gold_star_adjudication_ledger.sql"
        ).read_text(encoding="utf-8")
        connection.execute(migration, prepare=False)
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
