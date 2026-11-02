#!/usr/bin/env python3
"""Self-check of the repo tools on a temporary folder: python3 scripts/test_phi.py"""
import gzip
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_master_report as build  # noqa: E402
import import_snapshot as imp  # noqa: E402
import phi_lib as lib  # noqa: E402
import restore_duplicates as restore  # noqa: E402
import validate_evidence as val  # noqa: E402

# Fake values built at run time so that the repo scan does not trip on this file.
FAKE_ETHERSCAN = "A" * 8 + "B" * 26
FAKE_GH = "gh" + "p_" + "x" * 36


def test_scan():
    assert "url_key" in lib.scan_bytes(f"https://x/api?module=a&apikey={FAKE_ETHERSCAN}".encode())
    assert "github_token" in lib.scan_bytes(FAKE_GH.encode())
    assert "profile_fields" in lib.scan_bytes(b'{"proxyWallet":"0x1","pseudonym":"Someone","bio":"text"}')
    assert "private_key_block" in lib.scan_bytes(b"-----BEGIN " + b"PRIVATE KEY-----")
    assert lib.scan_bytes(b'{"pseudonym":"","bio":""}') == []
    assert lib.scan_bytes(b'key = os.environ["ETHERSCAN_API_KEY"]\napi_key=None') == []
    assert lib.scan_bytes(b"tx 0x" + b"a" * 64) == []
    assert lib.scan_bytes(b"apikey=net._key_from_env()") == []
    assert "key_assignment" in lib.scan_bytes(b"apikey=ABCDEFGHIJKLMNOPQRSTUVWX\n")
    assert lib.scan_bytes(b"secret value here", {b"secret value here": "MY_KEY"}) == ["known_secret:MY_KEY"]


def test_env_filter():
    assert lib.is_sensitive_env("HELIUS_KEY", "abcdefghijklmnop")
    assert lib.is_sensitive_env("RPC_URL", "https://rpc.example.com/?api-key=" + "a" * 24)
    assert lib.is_sensitive_env("DATABASE_URL", "postgres://user:pw@host/db")
    assert not lib.is_sensitive_env("POLYMARKET_DATA_API", "https://data-api.polymarket.com")
    assert not lib.is_sensitive_env("POLYMARKET_WS_URL", "wss://ws-subscriptions-clob.polymarket.com/ws/")
    assert not lib.is_sensitive_env("SOURCE_WALLET", "A" * 44)
    assert lib.is_sensitive_env("POLYMARKET_PROXY_ADDRESS", "0x" + "a" * 40)
    assert not lib.is_sensitive_env("TG_OWNER", "someusername123")


def test_numbers_and_findings():
    assert val.normalize_numbers("304 137,63") == "304137.63"
    assert val.normalize_numbers("304,137.63") == "304137.63"
    text = ("## F-001 | SUPPORTED | Une phrase\n- Sources: sources/a.md ; tx 0xabc\n- Method: m\n- Limits: l\n- Links: aucun\n"
            "\n## Manque pour conclure\n- une chose\n")
    findings, sections = lib.parse_findings(text)
    assert findings[0]["level"] == "SUPPORTED" and findings[0]["Sources"].startswith("sources/a.md")
    assert sections["Manque pour conclure"] == ["une chose"]
    assert val.cited_paths(findings[0]["Sources"]) == ["sources/a.md"]


def test_import_and_validate():
    with tempfile.TemporaryDirectory() as tmp:
        origin = Path(tmp) / "origin"
        repo = Path(tmp) / "repo"
        (origin / "tools").mkdir(parents=True)
        (origin / "state" / "http_cache").mkdir(parents=True)
        (origin / ".venv").mkdir()
        (origin / ".venv" / "x.py").write_text("x")
        (origin / ".env").write_text("K=v")
        (origin / "tools" / "a.py").write_text("print('ok')\n")
        (origin / "report.md").write_text("Montant 304 137,63 $, tx 0x" + "ab" * 32 + "\n")
        (origin / "secret.json").write_text(json.dumps({"url": f"https://x?apikey={FAKE_ETHERSCAN}"}))
        (origin / "profile.json").write_text(json.dumps({"pseudonym": "Someone", "bio": "text"}))
        with gzip.open(origin / "profile.json.gz", "wt") as fh:
            fh.write(json.dumps({"pseudonym": "Someone"}))
        (origin / "state" / "http_cache" / "r.json").write_text("{}")
        (origin / "big.csv").write_bytes(b"0" * (lib.MAX_FILE_BYTES + 1))
        (origin / "db.sqlite3").write_bytes(b"SQLite")
        os.symlink(origin / "report.md", origin / "link.md")
        before = {str(p): p.lstat().st_mtime for p in origin.rglob("*")}
        manifest = imp.import_investigation("t", origin, {}, {}, repo=repo, log=lambda *_: None)
        assert before == {str(p): p.lstat().st_mtime for p in origin.rglob("*")}, "l'origine a changé"
        status = {e["path"]: e["status"] for e in manifest["files"]}
        assert status["tools/a.py"] == "imported" and status["report.md"] == "imported"
        assert status["secret.json"] == "refused" and status["profile.json"] == "refused"
        assert status["profile.json.gz"] == "refused"
        assert status["state/http_cache/"] == "local_only" and status["big.csv"] == "local_only"
        assert status["db.sqlite3"] == "local_only" and status[".venv/"] == "excluded"
        assert status[".env"] == "excluded" and status["link.md"] == "excluded"
        hash_lines = gzip.open(repo / "investigations" / "t" / imp.HASH_LIST_NAME, "rt").read().splitlines()
        assert hash_lines == [lib.sha256_file(origin / "state/http_cache/r.json") + "  state/http_cache/r.json"]
        source = repo / "investigations" / "t" / "sources"
        assert (source / "tools" / "a.py").exists() and not (source / "secret.json").exists() and not (source / ".env").exists()
        for entry in manifest["files"]:
            if entry["status"] == "imported":
                assert lib.sha256_file(repo / entry["repo_path"]) == entry["sha256"]

        (origin / "tools" / "same_as_a.py").write_text("print('ok')\n")
        index = {}
        first = imp.import_investigation("t1", origin, {}, {}, repo=repo, dedupe_index=index, log=lambda *_: None)
        assert {e["path"]: e["status"] for e in first["files"]}["tools/same_as_a.py"] == "imported", "doublon interne perdu"
        imp.add_to_index(index, first)
        second = imp.import_investigation("t2", origin, {}, {}, repo=repo, dedupe_index=index, log=lambda *_: None)
        assert {e["path"]: e["status"] for e in second["files"]}["tools/a.py"] == "duplicate"
        real_repo, lib.REPO = lib.REPO, repo
        try:
            assert restore.restore(repo / "investigations" / "t2", Path(tmp) / "restored") > 0
            assert (Path(tmp) / "restored" / "tools" / "a.py").read_text() == "print('ok')\n"
        finally:
            lib.REPO = real_repo

        real = lib.REPO
        lib.REPO = repo
        val.lib.REPO = repo
        try:
            inv = repo / "investigations" / "t"
            good_tx = "0x" + "ab" * 32
            (inv / "README.md").write_text("# t\n")
            (inv / "STATUS.md").write_text("---\nid: t\ntitle: T\nstate: DONE\nupdated_utc: 2026-11-02T00:00:00Z\norigin: x\nversion: v\n---\n## Objectif\nO\n")
            (inv / "EVIDENCE.md").write_text("| Fichier | SHA-256 | Rôle |\n|---|---|---|\n| `sources/report.md` | auto | r |\n")
            (inv / "FINDINGS.md").write_text(f"## F-001 | CONFIRMED | Reçoit 304 137,63 $ par {good_tx}\n- Sources: sources/report.md\n- Method: m\n- Limits: l\n- Links: aucun\n")
            errors = []
            val.check_investigation(inv, {}, True, errors, {"t"})
            assert errors == [], errors
            assert "auto" not in (inv / "EVIDENCE.md").read_text()
            # A number or a hash absent from the cited source must be refused.
            (inv / "FINDINGS.md").write_text("## F-001 | CONFIRMED | Reçoit 999 999,99 $ par 0x" + "cd" * 32 + "\n- Sources: sources/report.md\n- Method: m\n- Limits: l\n- Links: aucun\n")
            errors = []
            val.check_investigation(inv, {}, False, errors, {"t"})
            assert sum("999" in e or "absent" in e for e in errors) == 2, errors
            # A file slipped into sources/ or altered must be refused.
            (inv / "sources" / "extra.txt").write_text("x")
            (inv / "sources" / "report.md").write_text("altered")
            errors = []
            val.check_manifest(inv, errors)
            assert any("hors manifeste" in e for e in errors) and any("empreinte" in e for e in errors), errors
        finally:
            lib.REPO = real
            val.lib.REPO = real


def test_report_sections():
    assert build.status_section("## Objectif\nA\nB\n## Limites\nC\n", "Objectif") == "A B"
    inv = [{"id": "x", "fields": {"state": "IN_PROGRESS", "title": "X", "version": "v", "updated_utc": "2026-11-02"},
            "body": "", "findings": [{"id": "F-001", "level": "SUPPORTED", "claim": "c", "Limits": "l", "Links": "y:F-002"}],
            "sections": {"Contradictions": ["une"]}, "manifest": {"files": [{"status": "local_only", "size": 5}], "counts": {}}}]
    text = build.report(inv)
    assert "provisoire" in text and "y:F-002" in text and "une" in text


if __name__ == "__main__":
    for name, func in list(globals().items()):
        if name.startswith("test_"):
            func()
            print("ok", name)
