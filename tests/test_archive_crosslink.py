import pytest

import archive_crosslink
from archive_crosslink import build_inventory, fetch_crosslink_documents, select_crosslinks


class FakeIndex:
    def __init__(self, records, stats_count=None):
        self.records = records
        self.calls = {}
        self.stats_count = len(records) if stats_count is None else stats_count

    def describe_index_stats(self):
        default_count = sum(1 for _, ns, _ in self.records if ns == "")
        other_count = sum(1 for _, ns, _ in self.records if ns == "cases")
        return {
            "total_vector_count": self.stats_count,
            "dimension": 384,
            "namespaces": {
                "__default__": {"vector_count": default_count},
                "cases": {"vector_count": other_count},
            },
        }

    def list_paginated(self, *, limit, pagination_token=None, namespace=""):
        records = [r for r in self.records if r[1] == namespace]
        if namespace == "" and pagination_token is None:
            page = records[:2]
            next_token = "page-2" if len(records) > 2 else None
        elif namespace == "" and pagination_token == "page-2":
            page = records[2:4]
            next_token = None
        else:
            page = records
            next_token = None
        return {
            "vectors": [{"id": item[0]} for item in page],
            "pagination": {"next": next_token},
        }

    def fetch(self, *, ids, namespace=""):
        return {
            "vectors": {
                vector_id: {"metadata": metadata}
                for vector_id, ns, metadata in self.records
                if vector_id in ids and ns == namespace
            }
        }


class FakeCore:
    @staticmethod
    def _use_corpus_access_eligible(metadata):
        return str(metadata.get("tier", "T1")).upper() != "T4" and str(metadata.get("access_class", "")).lower() != "protected"

    @staticmethod
    def _is_archived_canonical_resource(metadata):
        return str(metadata.get("lifecycle", "")).lower() in {"archived", "retired"}

    @staticmethod
    def _resource_content(metadata):
        return metadata.get("text", "")

    @staticmethod
    def _has_usable_destination(metadata):
        return str(metadata.get("url", "")).startswith("https://")

    @staticmethod
    def _is_navigable_canonical_resource(metadata):
        return FakeCore._use_corpus_access_eligible(metadata) and not FakeCore._is_archived_canonical_resource(metadata)


def _record(title, url, text, **extra):
    return {"title": title, "url": url, "text": text, **extra}


def test_inventory_walks_every_namespace_and_collapses_chunks_by_canonical_url():
    records = [
        ("v1", "", _record("Stewardship Governance", "https://geralddaquila.com/stewardship-governance/", "Governance and stewardship are linked.")),
        ("v2", "", _record("Stewardship Governance", "https://geralddaquila.com/stewardship-governance", "A second chunk for the same canonical asset.")),
        ("v3", "", _record("Stewardship Governance", "", "A chunk without its URL but with a unique canonical title.")),
        ("v4", "", _record("Institutional Correctability", "https://geralddaquila.com/institutional-correctability/", "Correction, review, and accountability.")),
        ("v5", "cases", _record("Protected Stewardship Codex", "https://geralddaquila.com/t4-codex/", "Protected content.", tier="T4")),
    ]
    index = FakeIndex(records)
    snapshot = build_inventory(index, FakeCore())
    assert snapshot["complete"] is True
    assert snapshot["expected_vector_count"] == 5
    assert snapshot["listed_vector_count"] == 5
    assert snapshot["fetched_vector_count"] == 5
    assert snapshot["asset_count"] == 2
    assert snapshot["ineligible_vector_count"] == 1
    assert snapshot["missing_url_asset_count"] == 0
    assert snapshot["crosslink_ready"] is True
    governance = next(a for a in snapshot["assets"] if "stewardship-governance" in a["url"])
    assert governance["vector_count"] == 3
    assert len(governance["vector_refs"]) == 3


def test_crosslink_selection_uses_full_inventory_but_excludes_existing_seed_url():
    records = [
        ("v1", "", _record("Stewardship Governance", "https://geralddaquila.com/stewardship-governance/", "Governance and stewardship.")),
        ("v2", "", _record("Institutional Correctability", "https://geralddaquila.com/institutional-correctability/", "Correction and accountability.")),
    ]
    snapshot = build_inventory(FakeIndex(records), FakeCore())
    selected = select_crosslinks(
        "stewardship governance",
        [{"title": "Stewardship Governance", "url": "https://geralddaquila.com/stewardship-governance/"}],
        snapshot,
    )
    assert selected == []


def test_selected_crosslink_is_fetched_and_revalidated_before_use():
    records = [
        ("v1", "", _record("Stewardship Governance", "https://geralddaquila.com/stewardship-governance/", "A substantial explanation of governance and stewardship across institutions.")),
        ("v2", "", _record("Institutional Correctability", "https://geralddaquila.com/institutional-correctability/", "Correction and accountability mechanisms help institutions learn.")),
    ]
    index = FakeIndex(records)
    snapshot = build_inventory(index, FakeCore())
    selected = select_crosslinks("institutional correctability", [], snapshot, limit=1)
    docs = fetch_crosslink_documents(index, FakeCore(), selected)
    assert len(docs) == 1
    assert docs[0]["title"] == "Institutional Correctability"
    assert docs[0]["url"] == "https://geralddaquila.com/institutional-correctability/"


def test_inventory_is_not_marked_complete_when_pinecone_counts_disagree():
    records = [
        ("v1", "", _record("Stewardship Governance", "https://geralddaquila.com/stewardship-governance/", "Governance.")),
    ]
    snapshot = build_inventory(FakeIndex(records, stats_count=2), FakeCore())
    assert snapshot["complete"] is False
    assert select_crosslinks("governance", [], snapshot) == []

def test_ambiguous_duplicate_titles_do_not_receive_guessed_urls():
    records = [
        ("v1", "", _record("Governance Foundations", "https://geralddaquila.com/governance-a/", "First canonical destination.")),
        ("v2", "", _record("Governance Foundations", "https://geralddaquila.com/governance-b/", "Second canonical destination.")),
        ("v3", "", _record("Governance Foundations", "", "Unlinked chunk with ambiguous title.")),
    ]
    snapshot = build_inventory(FakeIndex(records), FakeCore())
    assert snapshot["complete"] is True
    assert snapshot["missing_url_asset_count"] == 1
    assert snapshot["crosslink_ready"] is False
    assert select_crosslinks("governance foundations", [], snapshot) == []



def test_inventory_applies_request_timeouts_to_pinecone_operations():
    class TimeoutIndex:
        def __init__(self):
            self.timeout_calls = []

        def describe_index_stats(self, timeout=None):
            self.timeout_calls.append(("stats", timeout))
            return {
                "total_vector_count": 1,
                "dimension": 384,
                "namespaces": {"__default__": {"vector_count": 1}},
            }

        def list_paginated(self, *, limit, pagination_token=None, namespace="", timeout=None):
            self.timeout_calls.append(("list", timeout))
            return {"vectors": [{"id": "v1"}], "pagination": None}

        def fetch(self, *, ids, namespace="", timeout=None):
            self.timeout_calls.append(("fetch", timeout))
            return {
                "vectors": {
                    "v1": {
                        "metadata": _record(
                            "Stewardship Governance",
                            "https://geralddaquila.com/stewardship-governance/",
                            "Governance and stewardship.",
                        )
                    }
                }
            }

    index = TimeoutIndex()
    snapshot = build_inventory(index, FakeCore())
    assert snapshot["crosslink_ready"] is True
    assert index.timeout_calls == [
        ("stats", 15),
        ("list", 15),
        ("fetch", 15),
    ]


def test_inventory_fails_closed_when_pinecone_repeats_a_pagination_token():
    class RepeatingTokenIndex(FakeIndex):
        def list_paginated(self, *, limit, pagination_token=None, namespace=""):
            return {
                "vectors": [{"id": "v1"}],
                "pagination": {"next": "repeat-me"},
            }

    records = [
        ("v1", "", _record(
            "Stewardship Governance",
            "https://geralddaquila.com/stewardship-governance/",
            "Governance and stewardship.",
        )),
    ]
    with pytest.raises(RuntimeError, match="pagination token repeated"):
        build_inventory(RepeatingTokenIndex(records), FakeCore())



def test_visitor_crosslink_fetch_uses_short_timeout():
    class TimeoutIndex(FakeIndex):
        def __init__(self, records):
            super().__init__(records)
            self.fetch_timeouts = []

        def fetch(self, *, ids, namespace="", timeout=None):
            self.fetch_timeouts.append(timeout)
            return super().fetch(ids=ids, namespace=namespace)

    records = [
        ("v1", "", _record(
            "Institutional Correctability",
            "https://geralddaquila.com/institutional-correctability/",
            "Correction and accountability mechanisms help institutions learn.",
        )),
    ]
    index = TimeoutIndex(records)
    snapshot = build_inventory(index, FakeCore())
    selected = select_crosslinks("institutional correctability", [], snapshot, limit=1)
    docs = fetch_crosslink_documents(index, FakeCore(), selected)
    assert len(docs) == 1
    assert index.fetch_timeouts == [15, 5]



def test_full_corpus_refresh_is_primary_only_on_render():
    from archive_crosslink import should_start_refresh

    assert should_start_refresh("srv-da98sm2jnfac73d2ki5g") is True
    assert should_start_refresh("srv-db2s2bid0e5s73e7gt9g") is False
    assert should_start_refresh(None) is True
    assert should_start_refresh("") is True



def test_inventory_reports_url_aliases_without_treating_them_as_canonical():
    records = [
        ("v1", "", {
            "title": "Stewardship Governance",
            "permalink": "https://geralddaquila.com/stewardship-governance/",
            "text": "Governance and stewardship.",
        }),
    ]
    snapshot = build_inventory(FakeIndex(records), FakeCore())
    assert snapshot["metadata_key_counts"]["permalink"] == 1
    assert snapshot["url_field_presence"]["permalink"] == 1
    assert snapshot["missing_url_asset_count"] == 1
    assert snapshot["crosslink_ready"] is False



def test_wp_id_and_exact_title_recover_canonical_url(monkeypatch):
    title = "Stewardship Governance"
    canonical_url = "https://geralddaquila.com/stewardship-governance/"
    monkeypatch.setattr(
        archive_crosslink,
        "_load_wp_canonical_map",
        lambda: {"123": {"url": canonical_url, "title_key": archive_crosslink._canonical_title_key(title)}},
    )
    records = [("v1", "", _record(title, "", "Governance and stewardship.", wp_id=123))]
    snapshot = build_inventory(FakeIndex(records), FakeCore())
    assert snapshot["complete"] is True
    assert snapshot["crosslink_ready"] is True
    assert snapshot["missing_url_asset_count"] == 0
    assert snapshot["wp_id_url_recovered_vector_count"] == 1
    assert snapshot["assets"][0]["url"] == canonical_url.rstrip("/").casefold()


def test_wp_id_url_recovery_fails_closed_on_title_mismatch(monkeypatch):
    title = "Stewardship Governance"
    monkeypatch.setattr(
        archive_crosslink,
        "_load_wp_canonical_map",
        lambda: {"123": {
            "url": "https://geralddaquila.com/different-resource/",
            "title_key": archive_crosslink._canonical_title_key("Different Resource"),
        }},
    )
    records = [("v1", "", _record(title, "", "Governance and stewardship.", wp_id=123))]
    snapshot = build_inventory(FakeIndex(records), FakeCore())
    assert snapshot["wp_id_url_recovered_vector_count"] == 0
    assert snapshot["wp_id_title_mismatch_vector_count"] == 1
    assert snapshot["missing_url_asset_count"] == 1
    assert snapshot["crosslink_ready"] is False



def test_wordpress_registry_loads_published_post_and_page_identity(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            import json
            return json.dumps(self.payload).encode("utf-8")

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout))
        if "/posts?" in request.full_url:
            return Response([{
                "id": 123,
                "link": "https://geralddaquila.com/stewardship-governance/",
                "title": {"rendered": "Stewardship <em>Governance</em>"},
            }])
        return Response([{
            "id": 456,
            "link": "https://geralddaquila.com/the-world-he-carried/",
            "title": {"rendered": "The World He Carried"},
        }])

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(archive_crosslink, "urlopen", fake_urlopen)
    monkeypatch.setattr(archive_crosslink, "_WP_CANONICAL_CACHE", {})
    monkeypatch.setattr(archive_crosslink, "_WP_CANONICAL_CACHE_AT", 0.0)

    registry = archive_crosslink._load_wp_canonical_map()
    assert registry["123"]["url"] == "https://geralddaquila.com/stewardship-governance"
    assert registry["123"]["title_key"] == "stewardship governance"
    assert registry["456"]["url"] == "https://geralddaquila.com/the-world-he-carried"
    assert len(calls) == 2
    assert all(timeout == 3.0 for _, timeout in calls)



def test_inventory_retries_transient_missing_fetch_vectors():
    class FlakyFetchIndex(FakeIndex):
        def __init__(self, records):
            super().__init__(records)
            self.fetch_attempts = 0

        def fetch(self, *, ids, namespace=""):
            self.fetch_attempts += 1
            if self.fetch_attempts == 1:
                return {"vectors": {}}
            return super().fetch(ids=ids, namespace=namespace)

    records = [("v1", "", _record(
        "Stewardship Governance",
        "https://geralddaquila.com/stewardship-governance/",
        "Governance and stewardship.",
    ))]
    index = FlakyFetchIndex(records)
    snapshot = build_inventory(index, FakeCore())
    assert index.fetch_attempts == 2
    assert snapshot["complete"] is True
    assert snapshot["fetched_vector_count"] == 1
    assert snapshot["unfetched_vector_count"] == 0


def test_inventory_deduplicates_repeated_ids_across_pages():
    class DuplicateListIndex(FakeIndex):
        def list_paginated(self, *, limit, pagination_token=None, namespace=""):
            if namespace != "":
                return {"vectors": [], "pagination": None}
            if pagination_token is None:
                return {"vectors": [{"id": "v1"}], "pagination": {"next": "next-page"}}
            return {"vectors": [{"id": "v1"}], "pagination": None}

    records = [("v1", "", _record(
        "Stewardship Governance",
        "https://geralddaquila.com/stewardship-governance/",
        "Governance and stewardship.",
    ))]
    snapshot = build_inventory(DuplicateListIndex(records), FakeCore())
    assert snapshot["complete"] is True
    assert snapshot["listed_vector_count"] == 2
    assert snapshot["unique_listed_vector_count"] == 1
    assert snapshot["duplicate_listed_vector_count"] == 1
