"""Runtime source identity must cover supporting modules, not only main.py."""

import hashlib
from pathlib import Path

import main


def test_runtime_manifest_changes_when_a_supporting_runtime_module_changes(tmp_path):
    (tmp_path / "main.py").write_text("entrypoint = True\n", encoding="utf-8")
    provider = tmp_path / "provider_bank.py"
    provider.write_text("provider = 'first'\n", encoding="utf-8")
    first = main._runtime_source_manifest_sha256(tmp_path)

    provider.write_text("provider = 'second'\n", encoding="utf-8")
    second = main._runtime_source_manifest_sha256(tmp_path)

    assert first != second


def test_runtime_manifest_is_deterministic_and_excludes_test_only_files(tmp_path):
    (tmp_path / "main.py").write_text("entrypoint = True\n", encoding="utf-8")
    provider = tmp_path / "provider_bank.py"
    provider.write_text("provider = 'stable'\n", encoding="utf-8")
    first = main._runtime_source_manifest_sha256(tmp_path)

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_only.py").write_text("not runtime code\n", encoding="utf-8")
    qa = tmp_path / "QA"
    qa.mkdir()
    (qa / "audit.py").write_text("not runtime code\n", encoding="utf-8")
    second = main._runtime_source_manifest_sha256(tmp_path)

    assert first == second


def test_production_source_identity_is_not_the_main_file_hash():
    main_hash = hashlib.sha256(Path(main.__file__).resolve().read_bytes()).hexdigest()
    assert main.RUNTIME_SOURCE_SHA256 != main_hash
