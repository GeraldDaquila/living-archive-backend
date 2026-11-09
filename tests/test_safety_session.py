import safety_session


def test_signed_safety_session_round_trip(monkeypatch):
    monkeypatch.setattr(safety_session, "_SECRET", b"test-secret")
    token = safety_session.issue_safety_session(
        state="acute_contact",
        question="Can you contact emergency or crisis support now?",
        request_id="request-1",
    )
    verified = safety_session.verify_safety_session(token)
    assert verified == {
        "state": "acute_contact",
        "question": "Can you contact emergency or crisis support now?",
    }


def test_tampered_safety_session_is_rejected(monkeypatch):
    monkeypatch.setattr(safety_session, "_SECRET", b"test-secret")
    token = safety_session.issue_safety_session(
        state="acute",
        question="Have you moved away from anything you could use to hurt yourself?",
    )
    tampered = token[:-2] + "xx"
    assert safety_session.verify_safety_session(tampered) is None


def test_safety_session_contains_no_visitor_text(monkeypatch):
    monkeypatch.setattr(safety_session, "_SECRET", b"test-secret")
    visitor_text = "I don't want to live anymore and here is private detail"
    token = safety_session.issue_safety_session(
        state="current",
        question="Do you think you might act on these thoughts right now?",
        request_id=visitor_text,
    )
    assert visitor_text not in token
