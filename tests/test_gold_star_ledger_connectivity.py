import unittest
from unittest.mock import MagicMock

from gold_star_ledger_connectivity import DATABASE_URL_ENV, probe_database


class GoldStarLedgerConnectivityTests(unittest.TestCase):
    def test_missing_or_placeholder_configuration_fails_closed(self):
        self.assertEqual(probe_database({}), (False, "not_configured"))
        self.assertEqual(
            probe_database({DATABASE_URL_ENV: "PENDING_RENDER_PRIVATE_DATABASE_URL"}),
            (False, "not_configured"),
        )

    def test_success_runs_only_read_only_select_one_with_short_timeout(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connector = MagicMock()
        connector.connect.return_value.__enter__.return_value = connection

        result = probe_database({DATABASE_URL_ENV: "postgresql://private.invalid/db"}, connector)

        self.assertEqual(result, (True, "connected"))
        connector.connect.assert_called_once_with(
            "postgresql://private.invalid/db",
            connect_timeout=3,
            options="-c default_transaction_read_only=on",
            application_name="use_gold_star_ledger_connectivity_probe",
        )
        cursor.execute.assert_called_once_with("SELECT 1")

    def test_failure_does_not_expose_exception_details(self):
        connector = MagicMock()
        connector.connect.side_effect = RuntimeError(
            "password=do-not-leak host=private.internal"
        )
        result = probe_database(
            {DATABASE_URL_ENV: "postgresql://sensitive"}, connector
        )
        self.assertEqual(result, (False, "connection_failed"))
        self.assertNotIn("do-not-leak", result[1])
        self.assertNotIn("private.internal", result[1])

    def test_unexpected_query_result_fails_closed(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = (0,)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        connector = MagicMock()
        connector.connect.return_value.__enter__.return_value = connection
        self.assertEqual(
            probe_database({DATABASE_URL_ENV: "postgresql://private.invalid/db"}, connector),
            (False, "unexpected_result"),
        )


if __name__ == "__main__":
    unittest.main()
