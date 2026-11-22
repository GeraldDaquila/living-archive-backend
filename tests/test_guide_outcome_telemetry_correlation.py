"""Request correlation contract for privacy-minimized Guide outcome telemetry."""
import pytest
import general_guide_composition as composition


def test_provider_rejection_outcome_includes_opaque_request_and_attempt_context(monkeypatch, capsys):
    logged = []
    monkeypatch.setattr(
        composition,
        "_current_gold_star_request_context",
        lambda: {
            "request_id": "a" * 32,
            "request_ledger_version": "2",
        },
    )
    monkeypatch.setattr(
        composition,
        "_current_gold_star_attempt_trace",
        lambda: {"request_id": "a" * 32, "attempt_ordinal": 3},
    )
    monkeypatch.setattr(
        composition,
        "_current_gold_star_provider_route_context",
        lambda: {
            "provider_route_ordinal": 2,
            "attempt_count": 1,
            "terminal_state": "in_progress",
        },
    )
    monkeypatch.setattr(composition._TELEMETRY_LOG, "info", logged.append)

    composition._emit_guide_outcome(
        "provider_hard_rejection",
        reason="provider_response_embedded_navigation_URLs_in_visitor_prose",
    )

    emitted = capsys.readouterr().out.strip()
    assert "request_id=" + ("a" * 32) in emitted
    assert "request_ledger_version=2" in emitted
    assert "attempt_ordinal=3" in emitted
    assert "provider_route_ordinal=2" in emitted
    assert "provider_route_attempt_count=1" in emitted
    assert "provider_route_terminal_state=in_progress" in emitted
    assert logged == [emitted]
    assert "query=" not in emitted
    assert "response=" not in emitted


def test_explicit_request_correlation_is_not_overwritten(monkeypatch, capsys):
    monkeypatch.setattr(
        composition,
        "_current_gold_star_request_context",
        lambda: {"request_id": "a" * 32, "request_ledger_version": "2"},
    )
    monkeypatch.setattr(composition, "_current_gold_star_attempt_trace", lambda: None)
    monkeypatch.setattr(composition, "_current_gold_star_provider_route_context", lambda: {})
    monkeypatch.setattr(composition._TELEMETRY_LOG, "info", lambda _message: None)

    composition._emit_guide_outcome("gold_star_adjudication", request_id="b" * 32)

    emitted = capsys.readouterr().out.strip()
    assert "request_id=" + ("b" * 32) in emitted
    assert "request_id=" + ("a" * 32) not in emitted
    assert "request_ledger_version=2" in emitted


def test_import_time_structural_probe_rejection_is_not_logged_as_visitor_outcome(monkeypatch, capsys):
    logged = []
    monkeypatch.setattr(composition._TELEMETRY_LOG, "info", logged.append)
    parser = composition._parse_factory(
        [{"title": "Archive Doorway", "url": "https://geralddaquila.com/example/", "content": "Grounding material."}],
        emit_telemetry=False,
    )
    raw = (
        '{"response":"A useful answer with enough substance for a visitor.\\n\\n'
        '[Explore the Archive](https://geralddaquila.com/example/)",'
        '"doorway_title":"","response_shape":"general"}'
    )

    with pytest.raises(ValueError):
        parser(raw)

    emitted = capsys.readouterr().out
    assert "provider_hard_rejection" not in emitted
    assert "provider_soft_contract_bypass" not in emitted
    assert logged == []


def test_real_parser_rejection_inherits_active_request_correlation(monkeypatch, capsys):
    logged = []
    monkeypatch.setattr(
        composition,
        "_current_gold_star_request_context",
        lambda: {"request_id": "c" * 32, "request_ledger_version": "2"},
    )
    monkeypatch.setattr(
        composition,
        "_current_gold_star_attempt_trace",
        lambda: {"request_id": "c" * 32, "attempt_ordinal": 4},
    )
    monkeypatch.setattr(composition, "_current_gold_star_provider_route_context", lambda: {})
    monkeypatch.setattr(composition._TELEMETRY_LOG, "info", logged.append)
    parser = composition._parse_factory(
        [{"title": "Archive Doorway", "url": "https://geralddaquila.com/example/", "content": "Grounding material."}]
    )
    raw = (
        '{"response":"A useful answer with enough substance for a visitor.\\n\\n'
        '[Explore the Archive](https://geralddaquila.com/example/)",'
        '"doorway_title":"","response_shape":"general"}'
    )

    with pytest.raises(ValueError):
        parser(raw)

    emitted = capsys.readouterr().out.strip()
    assert "outcome=provider_hard_rejection" in emitted
    assert "request_id=" + ("c" * 32) in emitted
    assert "attempt_ordinal=4" in emitted
    assert logged == [emitted]
