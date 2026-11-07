import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["RUN_MODE"] = "dryrun"
from triagent import Store, accept_followups, parse_time, response_text, scan_wallet, extract_json, discover_next_tasks


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Store(Path(self.tmp.name) / "test.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_novelty_dedup_and_claim(self):
        first = self.db.enqueue("claude", "same-key-2026", "Check a transaction")
        self.assertTrue(first)
        self.assertIsNone(self.db.enqueue("claude", "same-key-2026", "Check a transaction again"))
        claimed = self.db.claim("claude")
        self.assertEqual(claimed["id"], first)
        self.assertIsNone(self.db.claim("claude"))

    def test_review_requires_novelty_and_max_children(self):
        jid = self.db.enqueue("claude", "one-case-2026", "Check a transaction")
        job = self.db.fetch(jid)
        followups = [{"agent": "grok", "novelty_key": "new-lead-1-2026", "task": "Find original source"},
                     {"agent": "claude", "novelty_key": "new-lead-2-2026", "task": "Replay funding"},
                     {"agent": "claude", "novelty_key": "new-lead-3-2026", "task": "Check base rate"}]
        self.assertEqual(accept_followups(self.db, job, {"novelty": 2, "approved_followups": followups}), 0)
        self.assertEqual(accept_followups(self.db, job, {"novelty": 5, "approved_followups": followups}), 2)
        self.assertEqual(accept_followups(self.db, job, {"novelty": 5, "approved_followups": followups}), 0)

    def test_first_wallet_scan_is_baseline_not_alert(self):
        import time
        sample = {"type": "TRADE", "side": "BUY", "usdc_size": 15000, "timestamp": int(time.time()),
                  "transaction_hash": "0x01", "condition_id": "0x02", "size": 1, "price": 0.5, "token_id": "1"}
        with patch("triagent.request_json", return_value={"data": [sample]}):
            self.assertEqual(scan_wallet(self.db, "0x" + "a"*40), 0)
            self.assertEqual(scan_wallet(self.db, "0x" + "a"*40), 0)
            sample2 = dict(sample, transaction_hash="0x03")
            with patch("triagent.request_json", return_value={"data": [sample2]}):
                self.assertEqual(scan_wallet(self.db, "0x" + "a"*40), 1)
                self.assertEqual(scan_wallet(self.db, "0x" + "a"*40), 0)

    def test_discovery_is_off_in_dryrun(self):
        self.assertEqual(discover_next_tasks(self.db), 0)

    def test_callback_nonce_auth(self):
        import asyncio
        import triagent
        from fastapi import HTTPException
        old_store = triagent.STORE
        triagent.STORE = self.db
        jid = self.db.enqueue("grok", "callback-case-2026", "Check primary tweet")
        self.db.update(jid, "awaiting_callback", nonce="verysecretnonce")
        report = triagent.GrokResult(job_id=jid, nonce="verysecretnonce", summary="Result")
        with patch.dict(os.environ, {"GROK_CALLBACK_SECRET": "serverkey"}):
            with self.assertRaises(HTTPException):
                asyncio.run(triagent.grok_complete(report, authorization="Bearer wrong"))
            self.assertTrue(asyncio.run(triagent.grok_complete(report, authorization="Bearer serverkey"))["accepted"])
            self.assertEqual(self.db.fetch(jid)["status"], "external_received")
        triagent.STORE = old_store

    def test_output_parsers(self):
        self.assertEqual(parse_time(1782752879000), 1782752879)
        self.assertEqual(response_text({"output": [{"content": [{"type": "output_text", "text": "ok"}]}]}), "ok")
        self.assertEqual(extract_json('```json\n{"a":1}\n```'), {"a": 1})


if __name__ == "__main__":
    unittest.main()
