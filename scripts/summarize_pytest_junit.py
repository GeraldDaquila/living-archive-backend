#!/usr/bin/env python3
"""Summarize pytest JUnit XML without guessing why a test failed."""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("junit_xml", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/failure-inventory.md"))
    args = parser.parse_args()

    root = ET.parse(args.junit_xml).getroot()
    cases = root.findall(".//testcase")
    failures = []
    errors = []
    skipped = []
    for case in cases:
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        nodeid = f"{classname}::{name}" if classname else name
        failure = case.find("failure")
        error = case.find("error")
        skip = case.find("skipped")
        if failure is not None:
            failures.append((nodeid, failure.attrib.get("message", ""), (failure.text or "").strip()))
        elif error is not None:
            errors.append((nodeid, error.attrib.get("message", ""), (error.text or "").strip()))
        elif skip is not None:
            skipped.append((nodeid, skip.attrib.get("message", "")))

    lines = [
        "# Pytest diagnostic inventory",
        "",
        f"- Test cases recorded: {len(cases)}",
        f"- Failures: {len(failures)}",
        f"- Errors: {len(errors)}",
        f"- Skipped: {len(skipped)}",
        "",
        "> All failures/errors below are UNRESOLVED pending contract-level review. This report does not classify or retire tests.",
        "",
        "## Failures",
        "",
    ]
    for nodeid, message, detail in failures:
        lines.extend([f"### `{nodeid}`", "", f"- Disposition: **UNRESOLVED**", f"- Failure: {message or '(see traceback)'}", ""])
        if detail:
            lines.extend(["```text", detail[:12000], "```", ""])
    lines.extend(["## Errors", ""])
    for nodeid, message, detail in errors:
        lines.extend([f"### `{nodeid}`", "", "- Disposition: **UNRESOLVED**", f"- Error: {message or '(see traceback)'}", ""])
        if detail:
            lines.extend(["```text", detail[:12000], "```", ""])
    lines.extend(["## Skipped", ""])
    for nodeid, message in skipped:
        lines.append(f"- `{nodeid}` — {message or 'no reason supplied'}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}: {len(failures)} failures, {len(errors)} errors, {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
