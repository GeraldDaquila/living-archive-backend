import subprocess

import pytest

from scripts import validate_gold_star_registry as validator


def test_missing_origin_main_ref_is_fetched_before_immutable_number_check(monkeypatch):
    calls = []
    verified = {"present": False}

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            if not verified["present"]:
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:3] == ["git", "fetch", "--no-tags"]:
            verified["present"] = True
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr(validator.subprocess, "run", fake_run)

    validator.ensure_canonical_main_ref()

    assert calls == [
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
        ["git", "fetch", "--no-tags", "origin", "main:refs/remotes/origin/main"],
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/main"],
    ]


def test_failed_fetch_keeps_registry_validation_fail_closed(monkeypatch):
    def fake_run(args, **kwargs):
        if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            raise subprocess.CalledProcessError(1, args)
        if args[:3] == ["git", "fetch", "--no-tags"]:
            return subprocess.CompletedProcess(args, 128, "", "remote unavailable")
        raise AssertionError(f"Unexpected git command: {args}")

    monkeypatch.setattr(validator.subprocess, "run", fake_run)

    with pytest.raises(SystemExit, match="cannot fetch canonical origin/main"):
        validator.ensure_canonical_main_ref()
