"""The archive readers on a small repository built by the test, then on the real checkout when it is there."""
import gzip
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from phi_forensics import archive, repository_root

REAL = Path(__file__).resolve().parents[2]
ROOT = repository_root()
W1, W2 = "0x" + "a1" * 20, "0x" + "b2" * 20
C1, C2 = "0x" + "c1" * 32, "0x" + "c2" * 32
MIXED = "0xAbCd" + "ef" * 18

WORKFLOW = """jobs:
  integrity:
    steps:
      - name: Check out
        uses: actions/checkout@v4
      - name: Say ok
        run: echo ok
      - name: Fail
        run: |
          echo before
          false
      - name: Slow
        run: sleep 30
      - name: Env
        env:
          K: v
        run: echo "$K"
      - name: Long
        run: seq 1 50
      - name: Guard
        env:
          PUBLICATION_BEFORE: ${{ github.event.before }}
        run: echo "$PUBLICATION_BEFORE"
      - name: Diff
        run: git diff --exit-code HEAD --
  other:
    steps:
      - name: Elsewhere
        run: echo no
"""
EARLY_ROWS = [
    {"initiator": W1, "condition_id": C1, "event_slug": "slug-a‮", "side": "YES", "t_alert": 100, "p_alert": 0.1, "lonely": True,
     "thin": True, "lonely_thin": True, "eval_set": "VALIDATION", "win": 1, "share15": 0.9},
    {"initiator": W2, "condition_id": C2, "event_slug": "slug-b", "side": "NO", "t_alert": 200, "p_alert": 0.2, "lonely": True,
     "thin": False, "lonely_thin": False, "eval_set": "DISCOVERY", "win": 0, "share15": 0.6},
    {"initiator": W1, "condition_id": C2, "event_slug": "slug-b", "side": "YES", "t_alert": 300, "p_alert": 0.3, "lonely": False,
     "thin": True, "lonely_thin": False, "eval_set": "VALIDATION", "win": 0, "share15": 0.1},
]
LATE_ROWS = [
    {"population": "validation_info", "class": "C1_FRESH_FUNDED_BET", "event": "16263", "t": 5, "price": 0.25, "win": 0, "entry_usd": 4010.4,
     "hours_to_end": 1.0},
    {"population": "validation_info", "class": "B1_BIG", "event": "17858", "t": 6, "price": 0.5, "win": 1, "entry_usd": 1632.62,
     "hours_to_end": 2.0},
    {"population": "discovery_info", "class": "C1_FRESH_FUNDED_BET", "event": "1", "t": 7, "price": 0.75, "win": 1, "entry_usd": 1000,
     "hours_to_end": 3.0},
]
LATE_VERDICT = {"comparisons_on_real_data": 63, "alpha_corrected": 0.0008,
                "classes": {"C1_FRESH_FUNDED_BET": {"verdict": "NOT_SUPPORTED_EFFECT_EXCLUDED"},
                            "B1_BIG": {"verdict": "NOT_SUPPORTED_UNDERPOWERED"}}}
FILES = {
    "README.md": f"# Root\n\nThe address {MIXED} is cited here.\n",
    "investigations/alpha/STATUS.md": ("---\nid: alpha\ntitle: Alpha case\nstate: DONE\nupdated_utc: 2026-11-01T00:00:00Z\n---\n\n"
                                       "## Objective\n\nx\n"),
    "investigations/alpha/FINDINGS.md": ("# Findings: alpha\n\n"
                                         "## F-001 | CONFIRMED | A Relay payment of 5 USDC\n- Sources: data/t.csv\n- Method: logs\n"
                                         "- Limits: one payment\n- Links: none\n\n"
                                         "## F-002 | REFUTED | One owner behind both wallets\n- Sources: data/t.csv\n- Method: owners read\n"
                                         "- Limits: none\n- Links: none\n\n"
                                         f"## F-003 | CONFIRMED | A second relay leg to {MIXED.lower()}\n- Sources: data/t.csv\n- Method: logs\n"
                                         "- Limits: one leg\n- Links: beta:F-001\n"),
    "investigations/beta/STATUS.md": "---\nid: beta\ntitle: Beta case\nstate: IN_PROGRESS\nupdated_utc: 2026-11-02T00:00:00Z\n---\n",
    "research_notes/note-1/README.md": "Intro line\n\n## Note one\n",
    "research_notes/note-1/data/t.csv": f"wallet,amount,bio,memo\n{W1},1.5,hello,ok‮\n{W2},2,x,y\n{W1.upper().replace('0X', '0x')},3,,z\n",
    "research_notes/note-1/data/arr.jsonl": "[1, 2]\n",
    "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl": "".join(json.dumps(r) + "\n" for r in EARLY_ROWS),
    "research_notes/early-detection-2026-11-13/study/derived/verdict.json": json.dumps({"verdict": "NOT_SUPPORTED"}),
    "research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl": "".join(json.dumps(r) + "\n" for r in LATE_ROWS),
    "research_notes/realtime-intelligence-2026-11-14/study/derived/verdict.json": json.dumps(LATE_VERDICT),
    ".github/workflows/repository-integrity.yml": WORKFLOW,
}


def git(root, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", *args], check=True, capture_output=True)


@unittest.skipUnless((REAL / "scripts" / "phi_lib.py").exists(), "the repository scripts are not present")
class Archive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = root = Path(cls.tmp.name).resolve()
        for name in ("phi_lib.py", "run_all_checks.py", "build_dataset_catalog.py"):
            (root / "scripts").mkdir(exist_ok=True)
            shutil.copy(REAL / "scripts" / name, root / "scripts" / name)
        for path, text in FILES.items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text, encoding="utf-8")
        with gzip.open(root / "research_notes/note-1/data/a.jsonl.gz", "wt", encoding="utf-8") as handle:
            handle.write('{"k": "v", "flag": true, "n": 3.5}\n{"k": "w", "flag": false, "n": 1}\n')
        (root / "research_notes/note-1/data/x.parquet").write_bytes(b"PAR1")
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "fixture")
        builder = archive._script(root, "build_dataset_catalog")
        (root / "datasets").mkdir()
        (root / archive.CATALOG).write_text(builder.render(builder.build(root)), encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # investigations and findings

    def test_investigations_count_findings_per_level_and_name_missing_files(self):
        zero = {"CONFIRMED": 0, "SUPPORTED": 0, "HYPOTHESIS": 0, "REFUTED": 0, "UNRESOLVED": 0}
        self.assertEqual(archive.investigations(self.root), [
            {"id": "alpha", "title": "Alpha case", "state": "DONE", "updated_utc": "2026-11-01T00:00:00Z",
             "findings": {**zero, "CONFIRMED": 2, "REFUTED": 1}, "path": "investigations/alpha", "missing": []},
            {"id": "beta", "title": "Beta case", "state": "IN_PROGRESS", "updated_utc": "2026-11-02T00:00:00Z", "findings": zero,
             "path": "investigations/beta", "missing": ["FINDINGS.md"]}])

    def test_findings_filter_on_claim_level_and_investigation(self):
        got = archive.findings(self.root, text="RELAY")
        self.assertEqual(([f["id"] for f in got["findings"]], got["matched"], got["cut"]), (["F-001", "F-003"], 2, False))
        self.assertEqual(got["findings"][0], {"id": "F-001", "level": "CONFIRMED", "claim": "A Relay payment of 5 USDC", "sources": "data/t.csv",
                                              "method": "logs", "limits": "one payment", "links": "none", "investigation": "alpha"})
        cut = archive.findings(self.root, text="relay", limit=1)
        self.assertEqual(([f["id"] for f in cut["findings"]], cut["matched"], cut["cut"]), (["F-001"], 2, True))
        self.assertEqual(archive.findings(self.root, level="REFUTED")["matched"], 1)
        self.assertEqual(archive.findings(self.root, investigation="beta"), {"findings": [], "matched": 0, "cut": False})

    def test_findings_refuse_an_unknown_level_investigation_or_limit(self):
        for kwargs in ({"level": "PROVEN"}, {"investigation": "gamma"}, {"limit": 0}, {"limit": True}):
            with self.assertRaises(ValueError):
                archive.findings(self.root, **kwargs)

    # address mentions

    def test_address_mentions_are_grouped_by_owner_in_any_case(self):
        got = archive.address_mentions(self.root, MIXED.lower())
        self.assertEqual((got["address"], got["files_total"], got["cut"]), (MIXED.lower(), 2, False))
        self.assertEqual(got["groups"], [{"owner": ".", "files": ["README.md"]},
                                         {"owner": "investigations/alpha", "files": ["investigations/alpha/FINDINGS.md"]}])
        self.assertIn("nor who controls it", got["limits"])
        cut = archive.address_mentions(self.root, MIXED, limit=1)
        self.assertEqual((cut["files_total"], cut["cut"], cut["groups"]), (2, True, [{"owner": ".", "files": ["README.md"]}]))
        self.assertEqual(archive.address_mentions(self.root, "0x" + "0" * 40)["files_total"], 0)

    def test_a_bad_address_is_refused_before_any_subprocess(self):
        with mock.patch.object(archive.subprocess, "run") as run:
            for bad in (MIXED[:-1], MIXED + "0", "0x" + "g" * 40, MIXED + "; rm -rf /", "-e", None):
                with self.assertRaises(ValueError):
                    archive.address_mentions(self.root, bad)
        self.assertEqual(run.call_count, 0)

    # checks

    def test_checks_are_the_offline_steps_of_the_integrity_job(self):
        self.assertEqual(archive.checks(self.root), [
            {"name": "Say ok", "command": "echo ok", "env": {}}, {"name": "Fail", "command": "echo before\nfalse", "env": {}},
            {"name": "Slow", "command": "sleep 30", "env": {}}, {"name": "Env", "command": 'echo "$K"', "env": {"K": "v"}},
            {"name": "Long", "command": "seq 1 50", "env": {}}])

    def test_run_check_reports_pass_failure_and_the_last_forty_lines(self):
        ok = archive.run_check(self.root, "Say ok")
        self.assertEqual((ok["name"], ok["passed"], ok["output_tail"]), ("Say ok", True, "ok"))
        self.assertEqual((archive.run_check(self.root, "Fail")["passed"], archive.run_check(self.root, "Fail")["output_tail"]), (False, "before"))
        self.assertEqual(archive.run_check(self.root, "Env")["output_tail"], "v")
        self.assertEqual(archive.run_check(self.root, "Long")["output_tail"], "\n".join(str(i) for i in range(11, 51)))

    def test_a_step_that_runs_too_long_is_killed_and_fails(self):
        got = archive.run_check(self.root, "Slow", timeout=0.5)
        self.assertFalse(got["passed"])
        self.assertEqual(got["output_tail"].splitlines()[-1], "timed out after 0.5 s")
        self.assertLess(got["seconds"], 5)

    def test_run_check_runs_nothing_that_is_not_an_offline_step_of_the_committed_workflow(self):
        workflow = self.root / ".github/workflows/repository-integrity.yml"
        workflow.write_text(WORKFLOW.replace("      - name: Say ok", "      - name: Injected\n        run: touch injected\n      - name: Say ok"),
                            encoding="utf-8")
        try:
            with mock.patch.object(archive.subprocess, "Popen", wraps=subprocess.Popen) as popen:
                for name in ("Injected", "Guard", "Diff", "Elsewhere", "Check out", "echo ok", "say ok", ""):
                    with self.assertRaises(ValueError):
                        archive.run_check(self.root, name)
            self.assertEqual({c.args[0][0] for c in popen.call_args_list}, {"git"})  # read the workflow, never ran a step
            self.assertNotIn("Injected", [c["name"] for c in archive.checks(self.root)])
        finally:
            workflow.write_text(WORKFLOW, encoding="utf-8")

    # tables

    def test_datasets_filter_the_catalogue_on_path_or_owner_title(self):
        everything = archive.datasets(self.root)
        self.assertEqual((everything["matched"], everything["cut"]), (6, False))
        note = archive.datasets(self.root, text="NOTE ONE")
        self.assertEqual([e["path"] for e in note["datasets"]], ["research_notes/note-1/data/a.jsonl.gz", "research_notes/note-1/data/arr.jsonl",
                                                                  "research_notes/note-1/data/t.csv", "research_notes/note-1/data/x.parquet"])
        self.assertEqual(archive.datasets(self.root, text="parquet", limit=1)["matched"], 1)
        self.assertEqual(archive.datasets(self.root, text=".jsonl", limit=2)["cut"], True)

    def test_query_dataset_matches_text_in_any_case_and_drops_profile_fields(self):
        got = archive.query_dataset(self.root, "research_notes/note-1/data/t.csv", where={"wallet": W1.upper().replace("0X", "0x")})
        self.assertEqual(got["rows"], [{"wallet": W1, "amount": "1.5", "memo": "ok"},
                                       {"wallet": W1.upper().replace("0X", "0x"), "amount": "3", "memo": "z"}])
        self.assertEqual((got["rows_scanned"], got["rows_matched"], got["cut"], got["scan_complete"], got["limit"]), (3, 2, False, True, 100))
        picked = archive.query_dataset(self.root, "research_notes/note-1/data/t.csv", columns=["amount"], limit=1)
        self.assertEqual((picked["rows"], picked["rows_matched"], picked["cut"]), ([{"amount": "1.5"}], 3, True))
        self.assertEqual(archive.query_dataset(self.root, "research_notes/note-1/data/t.csv", limit=10_000)["limit"], 500)

    def test_query_dataset_reports_a_scan_stopped_by_max_scan(self):
        stopped = archive.query_dataset(self.root, "research_notes/note-1/data/t.csv", max_scan=2)
        self.assertEqual((stopped["rows_scanned"], stopped["rows_matched"], stopped["scan_complete"]), (2, 2, False))
        whole = archive.query_dataset(self.root, "research_notes/note-1/data/t.csv", max_scan=3)
        self.assertEqual((whole["rows_scanned"], whole["scan_complete"]), (3, True))

    def test_query_dataset_reads_gzipped_json_lines_and_compares_json_values_as_text(self):
        got = archive.query_dataset(self.root, "research_notes/note-1/data/a.jsonl.gz", where={"flag": True})
        self.assertEqual((got["rows"], got["format"]), ([{"k": "v", "flag": True, "n": 3.5}], "jsonl.gz"))
        self.assertEqual(archive.query_dataset(self.root, "research_notes/note-1/data/a.jsonl.gz", where={"n": "1"})["rows"],
                         [{"k": "w", "flag": False, "n": 1}])
        self.assertEqual(archive.query_dataset(self.root, "research_notes/note-1/data/arr.jsonl")["rows"], [[1, 2]])

    def test_query_dataset_refusals(self):
        for path, kwargs in (("research_notes/note-1/data/x.parquet", {}), ("README.md", {}), ("../t.csv", {}), ("/etc/passwd", {}),
                             ("research_notes/note-1/data/../data/t.csv", {}), ("research_notes/note-1/data/t.csv", {"columns": ["bio"]}),
                             ("research_notes/note-1/data/t.csv", {"where": {"nope": "1"}}), ("research_notes/note-1/data/arr.jsonl", {"where": {"0": 1}}),
                             ("research_notes/note-1/data/t.csv", {"limit": 0}), ("research_notes/note-1/data/t.csv", {"max_scan": 0}), (None, {})):
            with self.assertRaises(ValueError, msg=(path, kwargs)):
                archive.query_dataset(self.root, path, **kwargs)

    # alerts

    def test_alerts_of_both_tables_carry_their_verdicts(self):
        got = archive.alerts(self.root)
        early, late = got["tables"]
        self.assertEqual((early["matched"], early["cut"], early["verdict"]), (3, False, {"verdict": "NOT_SUPPORTED"}))
        self.assertEqual(early["alerts"][0], {k: v for k, v in EARLY_ROWS[0].items() if k != "share15"} | {"event_slug": "slug-a"})
        self.assertEqual(late["alerts"], [
            {"population": "validation_info", "class": "C1_FRESH_FUNDED_BET", "event": "16263", "t": 5, "price": 0.25, "win": 0, "entry_usd": "4010.400000"},
            {"population": "validation_info", "class": "B1_BIG", "event": "17858", "t": 6, "price": 0.5, "win": 1, "entry_usd": "1632.620000"},
            {"population": "discovery_info", "class": "C1_FRESH_FUNDED_BET", "event": "1", "t": 7, "price": 0.75, "win": 1, "entry_usd": "1000.000000"}])
        self.assertEqual(late["verdict"], LATE_VERDICT)
        self.assertEqual(got["excluded"], [])
        self.assertIn("not a validated signal", got["reading"])
        self.assertIn("not evidence of inside information", got["reading"])

    def test_a_wallet_or_condition_filter_leaves_out_the_table_without_wallets(self):
        got = archive.alerts(self.root, wallet=W1.upper().replace("0X", "0x"))
        self.assertEqual([(a["t_alert"], a["initiator"]) for a in got["tables"][0]["alerts"]], [(100, W1), (300, W1)])
        self.assertEqual(len(got["tables"]), 1)
        self.assertEqual(got["excluded"], [{"table": archive.REALTIME_ALERTS, "reasons": ["its rows carry no wallet address"]}])
        both = archive.alerts(self.root, wallet=W1, condition=C2.upper().replace("0X", "0x"))
        self.assertEqual([a["t_alert"] for a in both["tables"][0]["alerts"]], [300])
        self.assertEqual(both["excluded"][0]["reasons"], ["its rows carry no wallet address", "its rows carry an event id, not a condition id"])

    def test_kind_selects_a_flag_of_one_study_or_a_class_of_the_other(self):
        lonely = archive.alerts(self.root, kind="LONELY")
        self.assertEqual([a["t_alert"] for a in lonely["tables"][0]["alerts"]], [100, 200])
        self.assertEqual(lonely["excluded"], [{"table": archive.REALTIME_ALERTS, "reasons": ["LONELY is not a class of this study"]}])
        big = archive.alerts(self.root, kind="B1_BIG", limit=1)
        self.assertEqual(big["excluded"], [{"table": f"{archive.EARLY}/analytic_table.jsonl", "reasons": ["B1_BIG is not a class of this study"]}])
        self.assertEqual(([a["event"] for a in big["tables"][0]["alerts"]], big["tables"][0]["verdict"]["classes"]),
                         (["17858"], {"B1_BIG": {"verdict": "NOT_SUPPORTED_UNDERPOWERED"}}))
        cut = archive.alerts(self.root, kind="C1_FRESH_FUNDED_BET", limit=1)["tables"][0]
        self.assertEqual((len(cut["alerts"]), cut["matched"], cut["cut"]), (1, 2, True))

    def test_alert_filters_are_validated(self):
        for kwargs in ({"wallet": "0x123"}, {"condition": "0x" + "zz" * 32}, {"condition": C1[:-2]}, {"kind": "lonely"}, {"kind": "NOPE"}, {"limit": -1}):
            with self.assertRaises(ValueError, msg=kwargs):
                archive.alerts(self.root, **kwargs)


@unittest.skipUnless(ROOT, "the repository checkout is not present")
class RealCheckout(unittest.TestCase):
    def test_findings_about_relay_exist(self):
        self.assertGreater(archive.findings(ROOT, text="Relay")["matched"], 0)

    def test_investigations_read_their_status(self):
        audit = next(i for i in archive.investigations(ROOT) if i["id"] == "ballon-dor-audit")
        self.assertEqual((audit["title"], audit["state"], audit["missing"]), ("Independent audit of the Ballon d'Or investigation", "DONE", []))

    def test_a_published_address_is_found_in_research_notes(self):
        got = archive.address_mentions(ROOT, "0xc5bb1be0407db7312911ec765d399d02461e411a")
        self.assertTrue(any(g["owner"].startswith("research_notes/") for g in got["groups"]))

    def test_an_address_of_the_wrong_length_is_refused_before_any_subprocess(self):
        with mock.patch.object(archive.subprocess, "run") as run, self.assertRaises(ValueError):
            archive.address_mentions(ROOT, "0xc5bb1be0407db7312911ec765d399d02461e411")
        self.assertEqual(run.call_count, 0)

    def test_checks_leave_out_the_event_guard_and_the_final_diff(self):
        names = [c["name"] for c in archive.checks(ROOT)]
        self.assertIn("Verify archived Relay trace", names)
        self.assertNotIn("Preserve accepted README and archived Relay evidence", names)
        self.assertNotIn("Ensure verification leaves tracked artifacts unchanged", names)

    def test_run_check_refuses_an_unknown_name(self):
        with self.assertRaises(ValueError):
            archive.run_check(ROOT, "python3 scripts/run_all_checks.py")

    def test_run_check_runs_one_real_step(self):
        got = archive.run_check(ROOT, "Verify archived Relay trace", timeout=120)
        self.assertTrue(got["passed"], got["output_tail"])

    def test_query_dataset_refuses_paths_outside_the_catalogue(self):
        for path in ("README.md", "../README.md", "research_notes/../README.md"):
            with self.assertRaises(ValueError):
                archive.query_dataset(ROOT, path)

    def test_archived_alerts_are_read_whole(self):
        early, late = archive.alerts(ROOT)["tables"]
        self.assertEqual((early["matched"], early["verdict"]["verdict"], late["matched"]), (587, "NOT_SUPPORTED", 6645))
        self.assertEqual(late["verdict"]["classes"]["C1_FRESH_FUNDED_BET"]["verdict"], "NOT_SUPPORTED_EFFECT_EXCLUDED")

    @unittest.skipUnless(ROOT and (ROOT / archive.CATALOG).exists(), "datasets/catalog.json not generated")
    def test_a_catalogued_table_can_be_queried(self):
        got = archive.query_dataset(ROOT, archive.REALTIME_ALERTS, where={"class": "c4_cofunded_group"})
        self.assertEqual((got["rows_matched"], got["rows_scanned"], got["scan_complete"]), (1, 6645, True))


if __name__ == "__main__":
    unittest.main()
