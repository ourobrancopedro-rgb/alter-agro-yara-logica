# tests/test_verify_hashes_discovery.py
import json
from pathlib import Path
import shutil
import types

import infra.github.verify_hashes as vh

def write(p: Path, content: str = "x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

def test_fail_when_file_not_in_ledger(tmp_path: Path, monkeypatch):
    # Arrange: estrutura mínima conforme allowlist
    root = tmp_path
    (root / "infra/github").mkdir(parents=True, exist_ok=True)
    # Arquivo novo permitido pela allowlist mas AUSENTE no ledger
    write(root / "docs/NEW_SPEC.md", "# spec")
    # Ledger vazio
    ledger = {}

    # Monkeypatch para rodar em tmp
    monkeypatch.chdir(root)

    # Act & Assert: deve falhar (missing_in_ledger)
    try:
        vh.verify(ledger)
    except SystemExit as e:
        assert e.code == 1
    else:
        raise AssertionError("Expected SystemExit(1) when ledger misses allowed files")

def test_fail_when_ledger_has_extra_entries(tmp_path: Path, monkeypatch):
    root = tmp_path
    monkeypatch.chdir(root)
    # Ledger aponta para arquivo que não é allowlisted
    ledger = {"private/runtime.py": "deadbeef" * 8}
    try:
        vh.verify(ledger)
    except SystemExit as e:
        assert e.code == 1
    else:
        raise AssertionError("Expected SystemExit(1) on extra ledger entries")

def test_pass_when_covered_and_hash_matches(tmp_path: Path, monkeypatch):
    root = tmp_path
    monkeypatch.chdir(root)
    # Arquivo permitido e ledger com hash correto
    p = root / "docs/OK.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("hello")
    h = vh.compute_hash(p)
    ledger = {"docs/OK.md": h}

    # Deve passar
    vh.verify(ledger)
