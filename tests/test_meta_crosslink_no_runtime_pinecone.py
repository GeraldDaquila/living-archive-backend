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
        PineconeMustNotBeCalled(),
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
