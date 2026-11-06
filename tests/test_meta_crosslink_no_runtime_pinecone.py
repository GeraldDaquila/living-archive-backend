import archive_crosslink


class PineconeMustNotBeCalled:
    def __getattr__(self, name):
        raise AssertionError(f"runtime meta-crosslink attempted Pinecone operation: {name}")


def test_missing_snapshot_fails_closed_without_starting_pinecone_inventory(monkeypatch):
    archive_crosslink._SNAPSHOT = None

    def forbidden_refresh(*args, **kwargs):
        raise AssertionError("visitor request must not start a Pinecone inventory refresh")

    monkeypatch.setattr(archive_crosslink, "start_refresh", forbidden_refresh)

    result = archive_crosslink.expand_context(
        "stewardship governance",
        [],
        PineconeMustNotBeCalled(),
        object(),
    )

    assert result == []


def test_v2_meta_crosslinks_are_selected_without_any_pinecone_operation(monkeypatch):
    archive_crosslink._SNAPSHOT = {
        "contract": "archive-crosslink-inventory-v2",
        "crosslink_ready": True,
        "source": "wordpress-canonical-registry",
        "assets": [
            {
                "title": "Stewardship Governance Architecture",
                "url": "https://geralddaquila.com/stewardship-governance-architecture",
                "resource_type": "page",
                "tier": "public",
                "access_class": "public",
                "summary": "",
            }
        ],
    }

    def forbidden_refresh(*args, **kwargs):
        raise AssertionError("v2 runtime navigation must not start Pinecone refresh")

    monkeypatch.setattr(archive_crosslink, "start_refresh", forbidden_refresh)

    result = archive_crosslink.expand_context(
        "stewardship governance",
        [],
        None,
        object(),
    )

    assert len(result) == 1
    assert result[0]["title"] == "Stewardship Governance Architecture"
    assert result[0]["crosslink_mode"] == "territorial_navigation"
    assert result[0]["content"] == ""


def test_legacy_v1_snapshot_is_not_allowed_to_fetch_pinecone_vectors(monkeypatch):
    archive_crosslink._SNAPSHOT = {
        "contract": "archive-crosslink-inventory-v1",
        "crosslink_ready": True,
        "assets": [
            {
                "title": "Stewardship Governance",
                "url": "https://geralddaquila.com/stewardship-governance",
                "vector_refs": [{"id": "vector-1", "namespace": ""}],
            }
        ],
    }

    def forbidden_refresh(*args, **kwargs):
        raise AssertionError("legacy snapshot must not initiate refresh")

    monkeypatch.setattr(archive_crosslink, "start_refresh", forbidden_refresh)

    result = archive_crosslink.expand_context(
        "stewardship governance",
        [],
        PineconeMustNotBeCalled(),
        object(),
    )

    assert result == []



def test_legacy_refresh_is_disabled_by_default_even_when_forced(monkeypatch):
    monkeypatch.delenv("ALLOW_LEGACY_PINECONE_CROSSLINK_REFRESH", raising=False)
    archive_crosslink._SNAPSHOT = None

    result = archive_crosslink.start_refresh(
        PineconeMustNotBeCalled(),
        object(),
        force=True,
    )

    assert result is False


def _remote_snapshot_payload():
    return {
        "contract": "archive-crosslink-inventory-v2",
        "crosslink_ready": True,
        "source": "wordpress-canonical-registry",
        "refreshed_at": __import__("time").time(),
        "assets": [{
            "title": "Stewardship Governance Architecture",
            "url": "https://geralddaquila.com/stewardship-governance-architecture",
            "resource_type": "page",
            "tier": "public",
            "access_class": "public",
            "summary": "Governance and stewardship architecture",
        }],
    }


def test_remote_v2_snapshot_requires_and_accepts_matching_sha256(monkeypatch):
    import hashlib
    import json

    raw = json.dumps(_remote_snapshot_payload(), separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit=-1):
            return self.body

    responses = iter([Response(raw.encode()), Response(digest.encode())])
    monkeypatch.setattr(archive_crosslink, "_snapshot_path", lambda: None)
    monkeypatch.setattr(archive_crosslink, "urlopen", lambda *_a, **_k: next(responses))
    archive_crosslink._SNAPSHOT = None

    assert archive_crosslink._load_persisted_snapshot() is True
    assert archive_crosslink._SNAPSHOT["contract"] == "archive-crosslink-inventory-v2"


def test_remote_snapshot_with_checksum_mismatch_is_rejected(monkeypatch):
    import json

    raw = json.dumps(_remote_snapshot_payload(), separators=(",", ":"))

    class Response:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit=-1):
            return self.body

    responses = iter([Response(raw.encode()), Response(("0" * 64).encode())])
    monkeypatch.setattr(archive_crosslink, "_snapshot_path", lambda: None)
    monkeypatch.setattr(archive_crosslink, "urlopen", lambda *_a, **_k: next(responses))
    archive_crosslink._SNAPSHOT = None

    assert archive_crosslink._load_persisted_snapshot() is False
    assert archive_crosslink._SNAPSHOT is None


def test_remote_snapshot_exceeding_size_limit_is_rejected(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit=-1):
            return b"x" * (limit + 1)

    monkeypatch.setattr(archive_crosslink, "_snapshot_path", lambda: None)
    monkeypatch.setattr(archive_crosslink, "urlopen", lambda *_a, **_k: Response())
    archive_crosslink._SNAPSHOT = None

    assert archive_crosslink._load_persisted_snapshot() is False
    assert archive_crosslink._SNAPSHOT is None
