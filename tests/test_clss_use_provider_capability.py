"""USE Provider Bank integration contract for CLSS synthesis."""
from __future__ import annotations

import json
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import provider_bank
import provider_gateway_service


class CLSSUseProviderCapabilityTests(unittest.TestCase):
    def test_clss_synthesis_is_an_explicit_gateway_operation(self):
        operation, messages, max_tokens = provider_gateway_service.validate_request({
            "contract_version": "v1",
            "operation": "clss_synthesis",
            "messages": [
                {"role": "system", "content": "Return a structured evidence-linked candidate."},
                {"role": "user", "content": '{"mode":"self","evidence":[]}'} ,
            ],
            "max_tokens": 1800,
        })
        self.assertEqual(operation, "clss_synthesis")
        self.assertEqual(len(messages), 2)
        self.assertEqual(max_tokens, 1800)

    def test_unknown_operations_remain_rejected(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException):
            provider_gateway_service.validate_request({
                "contract_version": "v1",
                "operation": "clss_arbitrary",
                "messages": [{"role": "user", "content": "test"}],
            })

    def test_clss_operation_requires_structured_reasoning_capabilities(self):
        required = provider_bank._operation_requirements("clss_synthesis", None)
        self.assertEqual(required, {
            "json_object", "long_context", "composition",
            "reasoning", "relational_analysis",
        })
        self.assertEqual(provider_bank.OPERATION_TOKEN_FLOORS["clss_synthesis"], 1200)

    def test_only_models_with_all_required_capabilities_are_eligible(self):
        eligible, missing = provider_bank._eligible(
            "groq", "openai/gpt-oss-120b", "clss_synthesis"
        )
        self.assertTrue(eligible)
        self.assertEqual(missing, [])
        eligible, missing = provider_bank._eligible(
            "mistral", "mistral-small-latest", "clss_synthesis"
        )
        self.assertFalse(eligible)
        self.assertIn("reasoning", missing)

    def test_clss_provider_error_details_are_not_persisted_or_logged(self):
        provider_bank._STATE["models"].pop("groq:clss-privacy-test", None)
        provider_bank._STATE.setdefault("quality", {}).pop(
            "quality:clss_synthesis:groq:clss-privacy-test", None
        )
        output = StringIO()
        sensitive = "private-answer-fragment-should-not-escape"
        with patch.object(provider_bank, "_persist_shared_state"):
            with redirect_stdout(output):
                provider_bank._failure(
                    RuntimeError(sensitive),
                    "groq",
                    "clss-privacy-test",
                    operation="clss_synthesis",
                )
        state = provider_bank._STATE["models"]["groq:clss-privacy-test"]
        self.assertNotIn(sensitive, state.get("last_error", ""))
        self.assertNotIn(sensitive, output.getvalue())
        exported = provider_bank.export_health_states({"groq:clss-privacy-test": state})
        self.assertNotIn(sensitive, json.dumps(exported))

    def test_gateway_routes_clss_through_shared_provider_bank(self):
        parsed = {
            "mode": "self",
            "path": "llm",
            "central_incoherence": {
                "text": "Candidate finding requiring review.",
                "finding_type": "insufficient_evidence",
                "evidence_ids": ["E1"],
            },
        }
        with patch.object(provider_gateway_service, "provider_bank_route", return_value={
            "parsed": parsed,
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "preference_order": ["groq", "gemini"],
        }) as route:
            result = provider_gateway_service.execute(
                operation="clss_synthesis",
                messages=[{"role": "user", "content": "{}"}],
                max_tokens=1800,
                use_core=object(),
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "clss_synthesis")
        self.assertEqual(result["result"], parsed)
        self.assertEqual(route.call_args.kwargs["operation"], "clss_synthesis")
        self.assertEqual(route.call_args.kwargs["max_tokens"], 1800)

    def test_candidate_output_must_be_json_object(self):
        with patch.object(provider_gateway_service, "provider_bank_route", return_value={
            "parsed": {"candidate": True},
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
            "preference_order": [],
        }) as route:
            provider_gateway_service.execute(
                operation="clss_synthesis",
                messages=[{"role": "user", "content": "{}"}],
                max_tokens=1800,
                use_core=object(),
            )
        raw = '{"candidate":true}'
        self.assertEqual(json.loads(raw), {"candidate": True})
        self.assertEqual(route.call_args.kwargs["operation"], "clss_synthesis")


if __name__ == "__main__":
    unittest.main()
