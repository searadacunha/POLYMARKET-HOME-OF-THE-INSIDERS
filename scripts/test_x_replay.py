"""Offline replay must not rewrite archived evidence or count skips as passes."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = (Path(__file__).resolve().parents[1] / "research_notes" /
          "x-history-2026-11-06" / "verification" / "verify.py")
spec = importlib.util.spec_from_file_location("historical_x_replay", SCRIPT)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class ReplayIntegrity(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.archived = self.root / "verification.json"
        self.archived.write_text('{"recorded_raw_replay":"keep original bytes"}\n')
        self.before = self.archived.read_bytes()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(replay, "HERE", self.root))
        self.stack.enter_context(patch.object(replay, "DATA", self.data))
        self.stack.enter_context(patch.object(replay, "RAW", self.root / "missing_raw"))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))

    def part_a(self, ok=True):
        return patch.object(replay, "part_a", side_effect=lambda: replay.check("A fixture", ok))

    def test_default_run_preserves_archive_and_reports_missing_raw(self):
        with self.part_a():
            self.assertEqual(replay.main([]), 0)
        self.assertEqual(self.archived.read_bytes(), self.before)
        self.assertTrue(any(detail.startswith("SKIPPED:") for _, _, detail in replay.RESULTS))

    def test_explicit_output_records_skip_separately_from_success(self):
        output = self.root / "current-run.json"
        with self.part_a():
            self.assertEqual(replay.main(["--output", str(output)]), 0)
        result = json.loads(output.read_text())
        self.assertEqual((result["checks"], result["failed"], result["skipped"]), (2, 0, 1))
        self.assertIsNone(result["results"][1]["pass"])
        self.assertEqual(self.archived.read_bytes(), self.before)

    def test_failed_current_check_is_not_hidden_by_an_old_success(self):
        output = self.root / "failed-run.json"
        with self.part_a(ok=False):
            self.assertEqual(replay.main(["--output", str(output)]), 1)
        self.assertEqual(json.loads(output.read_text())["failed"], 1)
        self.assertEqual(self.archived.read_bytes(), self.before)

    def test_existing_output_is_rejected_before_running_checks(self):
        with self.part_a() as checked, self.assertRaises(SystemExit):
            replay.main(["--output", str(self.archived)])
        checked.assert_not_called()
        self.assertEqual(self.archived.read_bytes(), self.before)

    def test_raw_recomputation_uses_temporary_outputs_even_when_it_disagrees(self):
        raw = self.root / "raw"
        raw.mkdir()
        original = self.data / "ballon_results.json"
        original.write_text('{"result":"accepted"}\n')
        before = original.read_bytes()
        temporary_outputs = []

        def fake_run(args, **kwargs):
            if Path(args[2]).name == "ana_ballon.py":
                target = Path(kwargs["env"]["XLEADS_OUTPUT_DIR"])
                self.assertNotEqual(target, self.data)
                temporary_outputs.append(target)
                (target / "ballon_results.json").write_text('{"result":"different"}')
                (target / "ballon_focus_positions.csv").write_text("new output\n")
            else:
                target = Path(args[3])
                self.assertNotEqual(target.parent, self.data)
                ledger = {wallet: {"trading_result": value} for wallet, value in zip(
                    args[4:], ("36933.71", "-5436.40", "841375.23", "-174453.49", "31863.48"))}
                target.write_text(json.dumps(ledger))
            return subprocess.CompletedProcess(args, 0)

        with self.part_a(), patch.object(replay, "RAW", raw), patch.object(replay.subprocess, "run", side_effect=fake_run):
            self.assertEqual(replay.main([]), 1)
        self.assertEqual(original.read_bytes(), before)
        self.assertEqual(self.archived.read_bytes(), self.before)
        self.assertFalse((self.data / "_verify_ledgers.json").exists())
        self.assertTrue(temporary_outputs)
        self.assertTrue(all(not path.exists() for path in temporary_outputs))


if __name__ == "__main__":
    unittest.main()
