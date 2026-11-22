"""One-shot, privacy-safe connectivity probe for the durable Gold Star ledger.

This module is deliberately not imported by the visitor request path. Run it
only from the primary Render service environment after configuring
GOLD_STAR_ADJUDICATION_DATABASE_URL with the Render private database URL.
"""
from __future__ import annotations

import os
import sys
from typing import Any

DATABASE_URL_ENV = "GOLD_STAR_ADJUDICATION_DATABASE_URL"
CONNECT_TIMEOUT_SECONDS = 3


def probe_database(environ: dict[str, str] | None = None, connector: Any = None) -> tuple[bool, str]:
    """Perform a read-only SELECT 1; never return or log connection details."""
    values = os.environ if environ is None else environ
    dsn = values.get(DATABASE_URL_ENV, "").strip()
    if not dsn or dsn == "PENDING_RENDER_PRIVATE_DATABASE_URL":
        return False, "not_configured"

    if connector is None:
        try:
            import psycopg as connector  # type: ignore[no-redef]
        except ImportError:
            return False, "driver_unavailable"

    try:
        with connector.connect(
            dsn,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
            options="-c default_transaction_read_only=on",
            application_name="use_gold_star_ledger_connectivity_probe",
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                if row != (1,):
                    return False, "unexpected_result"
        return True, "connected"
    except Exception:
        # Deliberately suppress exception text: drivers may include host,
        # database, username, or connection-string fragments in exceptions.
        return False, "connection_failed"


def main() -> int:
    ok, status = probe_database()
    print(f"gold_star_ledger_database_probe={status}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
