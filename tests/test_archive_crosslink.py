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
