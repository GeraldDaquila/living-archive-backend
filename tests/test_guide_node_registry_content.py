from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "wordpress" / "guide-node-registry" / "guide-node-registry.php"
TARGET_URL = (
    "https://geralddaquila.com/2025/05/21/"
    "political-dynasties-in-the-philippines-a-network-analysis-of-power-structures-and-their-socioeconomic-impacts/"
)


def test_political_dynasties_study_is_an_active_public_guide_node():
    source = REGISTRY_PATH.read_text(encoding="utf-8")
    marker = "'node_id'             => 'political-dynasties-philippines-study'"
    assert source.count(marker) == 1

    start = source.index(marker)
    end = source.index("\n        ),", start)
    node = source[start:end]

    assert "'title'               => 'Political Dynasties in the Philippines'" in node
    assert f"'canonical_url'       => '{TARGET_URL}'" in node
    assert "'asset_type'          => 'canonical_study'" in node
    assert "'access_class'        => 'public'" in node
    assert "'status'              => 'active'" in node
    assert "'parent'              => 'Philippine Systems, Society, and Culture'" in node
    for hint in (
        "political dynasties",
        "dynastic politics",
        "public accountability",
        "governance",
        "socioeconomic impacts",
        "power structures",
    ):
        assert f"'{hint}'" in node
