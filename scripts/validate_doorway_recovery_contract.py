#!/usr/bin/env python3
"""Fail closed if terminal deterministic recovery can return a navigational dead end."""
from pathlib import Path
SOURCE = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
MARKER = 'outer_visitor_boundary_deterministic_registered_recovery'
start = SOURCE.find(MARKER)
if start < 0:
    raise SystemExit("DOORWAY CONTRACT FAIL: terminal deterministic recovery path not found")
window = SOURCE[max(0, start - 2600): start + 900]
required = ["_select_guide_node_fallback_doorway(query)", "_normalize_authoritative_recommendation(_preserved)", 'safe["recommendation"] = _preserved']
missing = [item for item in required if item not in window]
if missing:
    raise SystemExit("DOORWAY CONTRACT FAIL: missing terminal safeguards: " + ", ".join(missing))
print("DOORWAY CONTRACT PASS: terminal recovery retains canonical fallback authority")
