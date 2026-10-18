import io
import json

import main


def test_guide_node_registry_refresh_busts_upstream_cache(monkeypatch):
    captured = {}
    payload = {
        "registry_version": main.GUIDE_NODE_REGISTRY_VERSION,
        "schema_version": "v2",
        "nodes": [],
    }

    monkeypatch.setattr(main.time, "time", lambda: 123456)
    monkeypatch.setattr(
        main,
        "UrlRequest",
        lambda url, headers, method: captured.update(
            {"url": url, "headers": headers, "method": method}
        ) or object(),
    )
    monkeypatch.setattr(
        main,
        "urlopen",
        lambda request, timeout: io.BytesIO(
            json.dumps(payload).encode("utf-8")
        ),
    )

    assert main._load_guide_node_registry() == []
    assert captured["url"] == (
        f"{main.GUIDE_NODE_REGISTRY_URL}?registry_refresh=123456"
    )
    assert captured["method"] == "GET"
    assert captured["headers"]["Cache-Control"] == "no-cache"
    assert captured["headers"]["Pragma"] == "no-cache"
