import copy
from pathlib import Path
import tempfile
import unittest

from radar import chain, context

Store = context.storage["Store"]


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = Store(self.root)
        self.addCleanup(self.store.close)
        self.alerts = str(self.root / "alerts.jsonl")
        self.record = {"id": "sealed", "market": {"condition_id": "0xabc"}, "trigger_t": 110, "emitted_t": 130}
        chain.append_locked(self.alerts, self.record)
        self.store.put("market", "123", {"condition_id": "0xABC", "event_id": "7"}, observed_at=80)
        self.url = "https://example.org/award"
        self.params = {"method": "GET"}
        self.ref = self.store.evidence(self.url, self.params, 200, b"official announcement", observed_at=125)
        self.payload = {"verified": True, "result_available": True, "event_id": "7", "milestone_type": "public_information",
                        "source_url": self.url, "evidence_id": self.ref, "public_at": 120}

    def read(self):
        return context.for_alert(self.alerts, "sealed", self.root / "data/polysentinel.sqlite3")

    def put(self, payload=None, at=128):
        self.store.put("public_milestone", "7", self.payload if payload is None else payload, observed_at=at)

    def test_verified_as_of_and_future_edits(self):
        self.put()
        self.put(dict(self.payload, public_at=99), 200)
        result = self.read()
        self.assertEqual(result["status"], "before_verified_public_information")
        self.assertEqual(result["received_at"], 125)
        self.assertEqual(result["evidence_id"], self.ref)

    def test_retroactive_or_unobserved_news(self):
        self.put(at=131)
        self.assertEqual(self.read()["status"], "unknown")
        self.put(at=121)
        self.assertEqual(self.read()["status"], "unknown")
        self.put(dict(self.payload, source_url="https://elsewhere.test"), 129)
        self.assertEqual(self.read()["status"], "unknown")

    def test_resolution_coverage_and_ambiguity(self):
        self.put(dict(self.payload, milestone_type="official_resolution"))
        self.assertEqual(self.read()["status"], "resolution_only")
        self.put(dict(self.payload, condition_ids=["0xother"]), 129)
        self.assertEqual(self.read()["status"], "unknown")
        self.put(dict(self.payload, public_at=105), 130)
        self.assertEqual(self.read()["status"], "after_public_information")
        self.put(dict(self.payload, public_at=103), 130)
        self.assertEqual(self.read()["status"], "unknown")

    def test_wrong_market_or_unverified_evidence(self):
        self.put()
        self.store.put("market", "234", {"condition_id":"0xabc", "event_id":"another"}, observed_at=102)
        self.assertEqual(self.read()["status"], "unknown")
        record = copy.deepcopy(self.record)
        record["market"]["condition_id"] = "other"
        self.assertEqual(context.assessment(self.store.conn, record)["status"], "unknown")

    def test_response_hash_and_status(self):
        bad = self.store.evidence(self.url, self.params, 503, b"unavailable", observed_at=125)
        self.put(dict(self.payload, evidence_id=bad))
        self.assertEqual(self.read()["status"], "unknown")
        self.put(at=129)
        self.store.conn.execute("UPDATE response_refs SET params='{}' WHERE id=?", (self.ref,))
        self.store.conn.commit()
        self.assertEqual(self.read()["status"], "unknown")
