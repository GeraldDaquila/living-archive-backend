"""Server boundary tests for the protected Formation specialist handoff."""

import asyncio
import json
import os
import unittest
from unittest import mock

from fastapi import HTTPException

import main


class FakeRequest:
    def __init__(self, body=b"", headers=None):
        self._body = body
        self.headers = headers or {}

    async def body(self):
        return self._body


class FormationEntranceSecurityTests(unittest.TestCase):
    def test_unauthenticated_direct_request_is_rejected_before_body_read(self):
        request = FakeRequest(body=b"not-json")
        with mock.patch.dict(os.environ, {"USE_PROVIDER_BANK_SHARED_SECRET": "test-secret"}):
            with self.assertRaises(HTTPException) as caught:
                asyncio.run(main._formation_entrance_route(request))
        self.assertEqual(caught.exception.status_code, 401)

    def test_missing_shared_secret_fails_closed(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("USE_PROVIDER_BANK_SHARED_SECRET", None)
            with self.assertRaises(HTTPException) as caught:
                asyncio.run(main._formation_entrance_route(FakeRequest(body=b"{}")))
        self.assertEqual(caught.exception.status_code, 503)

    def test_oversized_body_is_rejected_before_specialist_invocation(self):
        body = json.dumps({
            "choice": "continue",
            "situation": "x" * 9000,
            "possibility": "test",
        }).encode()
        request = FakeRequest(
            body=body,
            headers={"X-Living-Archive-Provider-Key": "test-secret"},
        )
        with mock.patch.dict(os.environ, {"USE_PROVIDER_BANK_SHARED_SECRET": "test-secret"}):
            with mock.patch.object(main, "invoke_specialist") as specialist:
                response = asyncio.run(main._formation_entrance_route(request))
        self.assertEqual(response.status_code, 413)
        specialist.assert_not_called()

    def test_field_length_limits_match_wordpress_spe_boundary(self):
        body = json.dumps({
            "choice": "continue",
            "situation": "x" * 3001,
            "possibility": "test",
            "source": main.FORMATION_ENTRANCE_SOURCE,
            "contract_version": main.FORMATION_ENTRANCE_CONTRACT_VERSION,
        }).encode()
        request = FakeRequest(
            body=body,
            headers={"X-Living-Archive-Provider-Key": "test-secret"},
        )
        with mock.patch.dict(os.environ, {"USE_PROVIDER_BANK_SHARED_SECRET": "test-secret"}):
            with mock.patch.object(main, "invoke_specialist") as specialist:
                response = asyncio.run(main._formation_entrance_route(request))
        self.assertEqual(response.status_code, 422)
        specialist.assert_not_called()


if __name__ == "__main__":
    unittest.main()
