import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

os.environ.pop("TRIAGENT_STATE", None)
from triagent import config as config_mod  # noqa: E402
from triagent.service import Supervisor  # noqa: E402
from triagent.store import Store  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


class Case(unittest.TestCase):
    mode = "dryrun"
    extra: dict = {}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="triagent-test-"))
        (self.tmp / "conf").mkdir()
        lines = {"RUN_MODE": self.mode, "DISK_MIN_FREE_GB": "0", "REPO_PATH": str(self.tmp / "repo"), **self.extra}
        (self.tmp / "conf" / "config.env").write_text("\n".join(f"{k}={v}" for k, v in lines.items()))
        (self.tmp / "repo").mkdir()
        self._env = {k: os.environ.pop(k) for k in list(os.environ) if k in config_mod.SECRET_NAMES}
        self.cfg = config_mod.load(self.tmp / "state", self.tmp / "conf")
        self.store = Store(self.cfg.db_path)
        self.sup = Supervisor(self.cfg, self.store)

    def tearDown(self):
        os.environ.update(self._env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def secrets(self, **values):
        (self.tmp / "conf" / "secrets.env").write_text("\n".join(f"{k}={v}" for k, v in values.items()))
        self.cfg = config_mod.load(self.tmp / "state", self.tmp / "conf")
        self.sup = Supervisor(self.cfg, self.store)


def verdict(novelty=4, decision="continue", followups=(), claims=()):
    return {"analysis": "test", "claims": list(claims), "novelty": novelty, "novelty_reason": "t",
            "duplicates_existing": [], "calculation_checks": [], "temporal_consistency": "ok",
            "falsification_tests": ["try X"], "decision": decision, "followups": list(followups), "risks": []}


def followup(agent, key, task="do it", kind=None):
    return {"agent": agent, "kind": kind or ("x_research" if agent == "grok" else "analysis"), "novelty_key": key,
            "task": task, "falsifier": "would refute", "expected_information_gain": 4, "est_cost_usd": 0.5}
