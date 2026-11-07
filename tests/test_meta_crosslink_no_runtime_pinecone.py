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



def test_v2_crosslink_selection_emits_privacy_safe_runtime_evidence_without_pinecone(monkeypatch, capsys):
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
        PineconeMustNotBeCalled(),
        object(),
    )
    output = capsys.readouterr().out
    assert len(result) == 1
    assert "USE archive meta-crosslink selection:" in output
    assert "selected=1" in output
    assert "query_token_count=2" in output
    assert "stewardship governance" not in output
