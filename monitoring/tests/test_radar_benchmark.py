"""The public offline measurement must reproduce when the monitor changes."""
from pathlib import Path
import subprocess
import sys
import unittest


class RadarBenchmark(unittest.TestCase):
    def test_committed_research(self):
        directory = Path(__file__).resolve().parents[2] / "research_notes/radar-asof-benchmark-2026-11-21"
        for script, args in (("benchmark.py", ["--check"]), ("case_replay.py", ["--check"]),
                             ("discovery.py", ["--check"]), ("verify_outputs.py", [])):
            with self.subTest(script=script):
                run = subprocess.run([sys.executable, "-I", str(directory / script), *args], capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
