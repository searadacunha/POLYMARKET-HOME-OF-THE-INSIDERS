import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from tests.base import Case, verdict
from triagent import fetch_tool, providers, schemas
from triagent.service import grok_callback
from triagent.store import MIGRATIONS, Store, now
from triagent.util import ProviderError, extract_json, redact, validate


class StoreTests(Case):
    def test_dedup_by_novelty_key(self):
        a = self.store.enqueue("claude", "analysis", "Same Key 2026", "task", origin="seed")
        self.assertTrue(a)
        self.assertIsNone(self.store.enqueue("claude", "analysis", "same   key 2026", "other", origin="seed"))
        self.assertEqual(self.store.claim("claude")["id"], a)
        self.assertIsNone(self.store.claim("claude"))

    def test_agent_kind_contract(self):
        with self.assertRaises(ValueError):
            self.store.enqueue("grok", "develop", "grok cannot develop 2026", "x", origin="seed")
        with self.assertRaises(ValueError):
            self.store.enqueue("claude", "x_research", "claude no x 2026", "x", origin="seed")

    def test_persistence_after_restart_and_idempotent_migrations(self):
        jid = self.store.enqueue("claude", "analysis", "survives restart 2026", "task", origin="seed")
        self.store.save_result(jid, {"report": {"summary": "kept"}})
        reopened = Store(self.cfg.db_path)
        self.assertEqual(reopened.schema_version(), len(MIGRATIONS))
        row = reopened.job(jid)
        self.assertEqual(row["status"], "reviewing")
        self.assertEqual(json.loads(row["result_json"])["report"]["summary"], "kept")
        self.assertTrue(reopened.integrity_ok())

    def test_backup_rotation(self):
        target = self.tmp / "backups"
        for _ in range(3):
            self.store.backup(target, keep=2)
        self.assertLessEqual(len(list(target.glob("*.sqlite3"))), 2)

    def test_divergent_verdicts_are_both_kept(self):
        inv = self.store.ensure_investigation("inv-divergence", "t")
        self.store.add_finding(inv, "job-a", "claim", "A paid B", tier="SUPPORTED")
        self.store.add_finding(inv, "job-b", "claim", "A paid B", tier="REFUTED")
        tiers = sorted(f["tier"] for f in self.store.findings(inv))
        self.assertEqual(tiers, ["REFUTED", "SUPPORTED"])


class RecoveryTests(Case):
    def _running(self, key, output: bool, pid=None):
        jid = self.store.enqueue("claude", "analysis", key, "task", origin="seed")
        self.store.claim("claude")
        mdir = self.cfg.missions_dir / jid
        (mdir / "evidence").mkdir(parents=True)
        (mdir / "MISSION.md").write_text("m")
        if output:
            (mdir / "claude_output.json").write_text(json.dumps(providers.fake_claude_output({"novelty_key": key})))
        self.store.set_status(jid, "running", "", mission_dir=str(mdir), pid=pid, session_id="s")
        return jid

    def test_interrupted_without_result_is_blocked_not_rerun(self):
        jid = self._running("interrupted mission 2026", output=False)
        self.sup.recover()
        job = self.store.job(jid)
        self.assertEqual(job["status"], "blocked")
        self.assertIn("billed", job["status_reason"])
        self.sup.tick_claude()
        self.assertEqual(self.store.job(jid)["attempts"], 1)  # never relaunched by itself

    def test_result_written_while_down_is_collected(self):
        jid = self._running("finished while down 2026", output=True)
        self.sup.recover()
        self.sup.tick_claude()
        self.assertEqual(self.store.job(jid)["status"], "reviewing")

    def test_live_mission_is_adopted(self):
        proc = subprocess.Popen(["/bin/sh", "-c", "sleep 30; true", "claude"])
        try:
            jid = self._running("still running 2026", output=False, pid=proc.pid)
            self.sup.recover()
            self.sup.tick_claude()
            self.assertEqual(self.store.job(jid)["status"], "running")
        finally:
            proc.kill()
            proc.wait()

    def test_grok_interrupted_during_sync_call_is_blocked(self):
        jid = self.store.enqueue("grok", "x_research", "grok sync interrupted 2026", "t", origin="seed")
        self.store.claim("grok")
        self.sup.recover()
        self.assertEqual(self.store.job(jid)["status"], "blocked")


class GateBudgetTests(Case):
    def test_budget_exhausted_blocks_dispatch(self):
        self.store.enqueue("claude", "analysis", "budget case 2026", "task", origin="seed")
        for _ in range(self.cfg.int("CLAUDE_MAX_MISSIONS_DAY")):
            self.store.add_cost("claude", 0.1, job_id=None, estimated=True)
        self.sup.tick_claude()
        self.assertEqual(self.store.counts().get("queued"), 1)
        self.assertIn("daily", self.sup.held("claude"))

    def test_pause_and_kill_switch(self):
        self.store.enqueue("claude", "analysis", "paused case 2026", "task", origin="seed")
        self.store.set_kv("paused", "1")
        self.sup.tick_claude()
        self.assertEqual(self.store.counts().get("queued"), 1)
        self.store.set_kv("paused", "0")
        self.cfg.kill_file.parent.mkdir(parents=True, exist_ok=True)
        self.cfg.kill_file.write_text("x")
        self.assertEqual(self.sup.gate(), "kill switch present")


class LiveCredentialTests(Case):
    mode = "live"

    def _reviewing(self, key="needs review 2026", agent="claude"):
        kind = "x_research" if agent == "grok" else "analysis"
        jid = self.store.enqueue(agent, kind, key, "task", origin="seed")
        mdir = self.cfg.missions_dir / jid
        (mdir / "evidence").mkdir(parents=True)
        self.store.set_status(jid, "running", "", mission_dir=str(mdir))
        self.store.save_result(jid, {"report": providers.fake_claude_output({"novelty_key": key})["structured_output"]})
        return jid

    def test_missing_openai_key_holds_and_keeps_result(self):
        jid = self._reviewing()
        with patch("triagent.polymarket.verify_reported_edges", return_value=[]):
            self.sup.tick_review()
        job = self.store.job(jid)
        self.assertEqual(job["status"], "reviewing")
        self.assertIn("OPENAI_API_KEY", job["status_reason"])
        self.assertIn("auth", self.sup.held("openai"))
        self.assertTrue(job["result_json"])

    def test_expired_openai_key(self):
        self.secrets(OPENAI_API_KEY="sk-test-expired-0000000000000000")
        jid = self._reviewing("expired key case 2026")
        with patch("triagent.providers.http", side_effect=ProviderError("auth", "HTTP 401: invalid key", 401)), \
                patch("triagent.polymarket.verify_reported_edges", return_value=[]):
            self.sup.tick_review()
        self.assertEqual(self.store.job(jid)["status"], "reviewing")
        self.assertTrue(self.sup.held("openai"))

    def test_missing_xai_key_requeues_grok(self):
        jid = self.store.enqueue("grok", "x_research", "grok without key 2026", "t", origin="seed")
        self.sup.tick_grok()
        self.assertEqual(self.store.job(jid)["status"], "queued")
        self.assertIn("XAI_API_KEY", self.sup.held("xai"))

    def test_uncertain_grok_call_is_not_retried_blindly(self):
        self.secrets(XAI_API_KEY="xai-test-0000000000000000")
        jid = self.store.enqueue("grok", "x_research", "grok timeout case 2026", "t", origin="seed")
        with patch("triagent.providers.http", side_effect=ProviderError("uncertain", "timeout")):
            self.sup.tick_grok()
        self.assertEqual(self.store.job(jid)["status"], "blocked")

    def test_review_prompt_never_carries_secrets_and_uses_strict_schema(self):
        key = "sk-live-secret-abcdefghijklmnop1234"
        self.secrets(OPENAI_API_KEY=key)
        jid = self._reviewing("secret leak case 2026")
        job = self.store.job(jid)
        captured = {}

        def fake_http(url, **kw):
            captured.update(kw)
            out = {"output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(verdict(1))}]}],
                   "usage": {"input_tokens": 10, "output_tokens": 10}}
            return 200, json.dumps(out).encode()
        report = {"summary": f"the key is {key}", "findings": []}
        with patch("triagent.providers.http", side_effect=fake_http):
            providers.review(self.cfg, self.store, job, report, {}, "")
        body = json.dumps(captured["body"])
        self.assertNotIn(key, body)
        self.assertEqual(captured["body"]["text"]["format"]["strict"], True)
        self.assertFalse(captured["body"]["store"])

    def test_openai_refusal_and_bad_schema_are_errors(self):
        refusal = {"output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]}
        with self.assertRaises(ProviderError):
            providers.parse_openai(refusal, schemas.REVIEW)
        bad = {"output": [{"type": "message", "content": [{"type": "output_text", "text": '{"novelty": 9}'}]}]}
        with self.assertRaises(ProviderError):
            providers.parse_openai(bad, schemas.REVIEW)

    def test_claude_auth_failure_requeues_and_holds(self):
        jid = self.store.enqueue("claude", "analysis", "claude auth case 2026", "t", origin="seed")
        job = self.store.claim("claude")
        mdir = self.cfg.missions_dir / jid
        mdir.mkdir(parents=True)
        (mdir / "claude_output.json").write_text(json.dumps({"type": "result", "subtype": "success", "is_error": True,
                                                             "result": "Not logged in · Please run /login"}))
        self.store.set_status(jid, "running", "", mission_dir=str(mdir))
        self.sup.finish_claude(self.store.job(jid))
        self.assertEqual(self.store.job(jid)["status"], "queued")
        self.assertTrue(self.sup.held("claude"))


class GrokBotTests(Case):
    extra = {"GROK_MODE": "bot"}

    def _awaiting(self):
        jid = self.store.enqueue("grok", "x_research", "bot mission 2026", "t", origin="seed")
        self.sup.tick_grok()
        job = self.store.job(jid)
        self.assertEqual(job["status"], "awaiting_external_result")
        return job

    def _post(self, auth, payload):
        raw = json.dumps(payload).encode()
        return grok_callback(self.sup, auth, io.BytesIO(raw), len(raw))

    def test_authenticated_callback_is_stored(self):
        self.secrets(GROK_CALLBACK_SECRET="callback-secret-123456")
        job = self._awaiting()
        body = {"job_id": job["id"], "nonce": job["external_nonce"], "summary": "found 2 posts",
                "leads": [], "unresolved": [], "proposed_tests": []}
        self.assertEqual(self._post("Bearer wrong", body)[0], 401)
        self.assertEqual(self._post("Bearer callback-secret-123456", {**body, "nonce": "bad"})[0], 403)
        self.assertEqual(self._post("Bearer callback-secret-123456", {**body, "extra": 1})[0], 400)
        code, res = self._post("Bearer callback-secret-123456", body)
        self.assertEqual((code, res["stored"]), (200, True))
        self.assertEqual(self.store.job(job["id"])["status"], "reviewing")
        self.assertEqual(self._post("Bearer callback-secret-123456", body)[0], 409)  # replay refused

    def test_missing_grok_result_fails_at_deadline(self):
        job = self._awaiting()
        self.store.execute("UPDATE jobs SET deadline=? WHERE id=?", (now() - 1, job["id"]))
        self.sup.tick_grok()
        row = self.store.job(job["id"])
        self.assertEqual(row["status"], "failed")
        self.assertIn("acknowledgement is not a completed task", row["status_reason"])


class SafetyTests(Case):
    def test_claude_mission_is_fresh_read_only_and_cannot_publish(self):
        jid = self.store.enqueue("claude", "analysis", "safety command 2026", "t", origin="seed")
        job = self.store.claim("claude")
        job["session_id"] = "00000000-0000-4000-8000-000000000000"
        mdir, _ = providers.prepare_mission(self.cfg, self.store, job)
        cmd = providers.claude_command(self.cfg, job, mdir, self.cfg.repo_dir)
        for flag in ("--safe-mode", "--restricted", "--no-session-persistence", "--strict-mcp-config"):
            self.assertIn(flag, cmd)
        for flag in ("--resume", "--continue", "-c", "--dangerously-skip-permissions"):
            self.assertNotIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "dontAsk")
        settings = json.loads((mdir / "claude_settings.json").read_text())
        self.assertIn("Bash(git credential *)", settings["permissions"]["deny"])
        self.assertIn("Bash(git push *)", settings["permissions"]["deny"])
        bash = [r for r in settings["permissions"]["allow"] if r.startswith("Bash")]
        self.assertEqual(len(bash), 1)
        self.assertIn("tg-fetch", bash[0])
        self.assertFalse(any(k in " ".join(settings["permissions"]["allow"]) for k in ("git", "gh ", "Edit", "Write")))
        env = providers.mission_env(self.cfg, mdir)
        self.assertFalse(set(env) & {"OPENAI_API_KEY", "XAI_API_KEY", "GROK_CALLBACK_SECRET"})

    def test_api_mode_uses_bare(self):
        self.cfg.values["CLAUDE_AUTH"] = "api"
        job = {"id": "x" * 16, "kind": "analysis", "session_id": "s"}
        (self.cfg.missions_dir / job["id"]).mkdir(parents=True)
        cmd = providers.claude_command(self.cfg, job, self.cfg.missions_dir / job["id"], self.cfg.repo_dir)
        self.assertIn("--bare", cmd)

    def test_no_code_path_pushes_or_merges(self):
        lines = [l for p in Path(providers.__file__).parent.glob("*.py") for l in p.read_text().splitlines()]
        git_calls = [l for l in lines if '"git"' in l or "subprocess" in l or '"gh"' in l]
        for line in git_calls:
            for forbidden in ("push", "merge", "--force", "reset"):
                self.assertNotIn(forbidden, line)
        self.assertFalse([l for l in lines if "gh pr" in l])

    def test_fetch_tool_refuses_other_hosts_and_write_methods(self):
        mdir = self.tmp / "mission"
        mdir.mkdir()
        (mdir / "MISSION.md").write_text("m")
        with patch.dict("os.environ", {"TRIAGENT_MISSION_DIR": str(mdir)}), patch("builtins.print"):
            self.assertEqual(fetch_tool.main(["get", "https://evil.example.com/x"]), 2)
            self.assertEqual(fetch_tool.main(["get", "http://data-api.polymarket.com/v2/trades"]), 2)
            self.assertEqual(fetch_tool.main(["rpc", "polygon", "eth_sendRawTransaction", "[]"]), 2)
            self.assertEqual(fetch_tool.main(["rpc", "solana", "sendTransaction", "[]"]), 2)

    def test_fetch_tool_archives_by_sha256(self):
        mdir = self.tmp / "mission2"
        mdir.mkdir()
        (mdir / "MISSION.md").write_text("m")
        with patch.dict("os.environ", {"TRIAGENT_MISSION_DIR": str(mdir)}), patch("builtins.print"), \
                patch("triagent.fetch_tool.call", return_value=(200, b'{"data": []}')):
            self.assertEqual(fetch_tool.main(["get", "https://data-api.polymarket.com/v2/trades?limit=1"]), 0)
        row = json.loads((mdir / "evidence" / "index.jsonl").read_text().splitlines()[0])
        report = {"findings": [{"evidence_ids": [row["sha256"], "made-up-id"]}]}
        check = providers.evidence_check(self.cfg, mdir, report)
        self.assertEqual((check["verified"], check["missing"]), ([row["sha256"]], ["made-up-id"]))
        (mdir / "evidence" / f"{row['sha256']}.raw").write_bytes(b"tampered")
        self.assertEqual(providers.evidence_check(self.cfg, mdir, report)["verified"], [])

    def test_untrusted_page_is_rendered_as_text(self):
        html = (Path(providers.__file__).parent / "ui.html").read_text()
        self.assertNotIn("innerHTML", html)


class UtilTests(Case):
    def test_parsers_and_validator(self):
        self.assertEqual(extract_json('prose ```json\n{"a": 1}\n``` more'), {"a": 1})
        self.assertEqual(extract_json('answer: {"a": 2} done'), {"a": 2})
        self.assertEqual(validate(verdict(), schemas.REVIEW), [])
        self.assertTrue(validate({**verdict(), "novelty": 9}, schemas.REVIEW))
        self.assertTrue(validate({**verdict(), "x": 1}, schemas.REVIEW))
        self.assertIn("[REDACTED]", redact("Authorization: Bearer abcdefghijklmnopqrstuv"))
        self.assertIn("apikey=[REDACTED]", redact("https://x?apikey=SECRET123"))


if __name__ == "__main__":
    import unittest
    unittest.main()
