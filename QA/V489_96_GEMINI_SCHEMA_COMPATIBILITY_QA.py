"""Regression tests for Gemini's provider-specific JSON Schema boundary."""
import provider_bank


def main():
    schema = {
        "type": "object",
        "properties": {
            "response": {"type": "string", "minLength": 1, "additionalProperties": False},
            "metadata": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "additionalProperties": True,
            },
        },
        "required": ["response", "metadata"],
        "additionalProperties": True,
    }
    actual = provider_bank._gemini_compatible_response_schema(schema)
    assert "additionalProperties" not in actual
    assert "additionalProperties" not in actual["properties"]["response"]
    assert "additionalProperties" not in actual["properties"]["metadata"]
    assert actual["properties"]["response"]["minLength"] == 1
    assert actual["required"] == ["response", "metadata"]

    # The live failure was a Gemini API 400 for this unsupported keyword.
    operation_schema = {
        "type": "object",
        "properties": {"response": {"type": "string"}},
        "required": ["response"],
        "additionalProperties": True,
    }
    assert "additionalProperties" not in provider_bank._gemini_compatible_response_schema(operation_schema)
    print("V489.96 GEMINI RESPONSE-SCHEMA COMPATIBILITY QA: PASS")


if __name__ == "__main__":
    main()
