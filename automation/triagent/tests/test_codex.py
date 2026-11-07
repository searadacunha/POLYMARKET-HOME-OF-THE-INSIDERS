"""OPENAI_MODE=codex_cli against a stand-in `codex` binary: every failure keeps the result and never mixes answers.
The real ChatGPT-subscription call is exercised by hand (README, "Real checks"), not here."""
import json
import stat
from unittest.mock import patch

from tests.base import Case, verdict
from triagent import providers

FAKE = r"""#!/bin/sh
dir=$(dirname "$0"); mode=$(cat "$dir/mode")
out=""; prev=""
for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done
printf '%s\n' "$@" > "$dir/args"
cat > "$dir/prompt"
rid=$(sed -n 's/.*request_id set to exactly "\([^"]*\)".*/\1/p' "$dir/prompt" | head -1)
done='{"type":"turn.completed","usage":{"input_tokens":5,"output_tokens":5}}'
echo '{"type":"thread.started","thread_id":"thread-1"}'
echo '{"type":"item.completed","item":{"type":"error","message":"Code Mode is unavailable"}}'
case $mode in
  ok) echo "$done"; sed "s/__RID__/$rid/" "$dir/answer" > "$out" ;;
  stale) echo "$done"; sed "s/__RID__/plan-000000000000/" "$dir/answer" > "$out" ;;
  truncated) echo "$done"; printf '{"request_id":"%s","analysis":"cut' "$rid" > "$out" ;;
  nologin) echo '{"type":"error","message":"Not logged in. Run codex login"}'; exit 1 ;;
  limit) echo '{"type":"turn.failed","error":{"message":"You have hit your usage limit. Try again later."}}'; exit 1 ;;
  slow) sleep 5 ;;
esac
"""


class CodexCliTests(Case):
    mode = "live"

    def setUp(self):
        self.extra = {"OPENAI_MODE": "codex_cli", "CODEX_TIMEOUT_S": "2"}
        super().setUp()
        self.bin = self.tmp / "fakebin"
        self.bin.mkdir()
        exe = self.bin / "codex"
        exe.write_text(FAKE)
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        (self.bin / "answer").write_text(json.dumps({"request_id": "__RID__", **verdict(1, "stop_no_new_information")}))
        self.conf(CODEX_BIN=exe)

    def conf(self, **values):
        with (self.tmp / "conf" / "config.env").open("a") as f:
            f.write("".join(f"\n{k}={v}" for k, v in values.items()) + "\n")
        self.secrets()

    def fake(self, mode):
        (self.bin / "mode").write_text(mode)

    def reviewing(self, key, summary="report"):
        jid = self.store.enqueue("claude", "analysis", key, "task", origin="seed")
        mdir = self.cfg.missions_dir / jid
        (mdir / "evidence").mkdir(parents=True)
        self.store.set_status(jid, "running", "", mission_dir=str(mdir))
        report = providers.fake_claude_output({"novelty_key": key})["structured_output"]
        self.store.save_result(jid, {"report": {**report, "summary": summary}})
        return jid

    def tick(self):
        with patch("triagent.polymarket.verify_reported_edges", return_value=[]):
            self.sup.tick_review()

    def test_real_shaped_answer_is_bound_hashed_and_stored(self):
        self.secrets(OPENAI_API_KEY="sk-live-secret-abcdefghijklmnop1234")
        self.fake("ok")
        jid = self.reviewing("codex ok 2026", "the key is sk-live-secret-abcdefghijklmnop1234")
        self.tick()
        job = self.store.job(jid)
        self.assertEqual(job["status"], "done", job["status_reason"])
        meta = json.loads(job["review_json"])["_provider"]
        self.assertEqual(meta["mode"], "codex_cli")
        self.assertTrue(meta["request_id"].startswith(jid))
        self.assertEqual(len(meta["answer_sha256"]), 64)
        args = (self.bin / "args").read_text().splitlines()
        for flag in ("--ignore-user-config", "--ephemeral", "--disable=code_mode_host", "--disable=shell_tool"):
            self.assertIn(flag, args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertNotIn("sk-live-secret", (self.bin / "prompt").read_text())
        self.assertEqual(self.store.spent("openai", 0), (0.0, 1))

    def test_answer_for_another_request_is_rejected(self):
        self.fake("stale")
        jid = self.reviewing("codex stale 2026")
        self.tick()
        job = self.store.job(jid)
        self.assertEqual((job["status"], job["review_attempts"]), ("reviewing", 1))

    def test_truncated_answer_is_rejected(self):
        self.fake("truncated")
        jid = self.reviewing("codex truncated 2026")
        self.tick()
        self.assertEqual(self.store.job(jid)["review_attempts"], 1)
        self.assertIsNone(self.store.job(jid)["review_json"])

    def test_expired_login_holds_and_keeps_result(self):
        self.fake("nologin")
        jid = self.reviewing("codex login 2026")
        self.tick()
        job = self.store.job(jid)
        self.assertEqual(job["status"], "reviewing")
        self.assertTrue(job["result_json"])
        self.assertIn("auth", self.sup.held("openai"))

    def test_usage_limit_is_a_transient_hold(self):
        self.fake("limit")
        self.reviewing("codex limit 2026")
        self.tick()
        self.assertIn("transient", self.sup.held("openai"))

    def test_timeout_is_uncertain_not_success(self):
        self.fake("slow")
        jid = self.reviewing("codex slow 2026")
        self.tick()
        self.assertEqual(self.store.job(jid)["review_attempts"], 1)
        self.assertEqual(self.store.job(jid)["status"], "reviewing")

    def test_missing_binary_is_an_auth_hold(self):
        self.conf(CODEX_BIN=f"{self.tmp}/nope/codex")
        self.reviewing("codex missing 2026")
        self.tick()
        self.assertIn("auth", self.sup.held("openai"))

    def test_chatgpt_gui_never_runs_and_says_why(self):
        self.conf(OPENAI_MODE="chatgpt_gui")
        self.fake("ok")
        jid = self.reviewing("gui blocked 2026")
        self.tick()
        self.assertFalse((self.bin / "args").exists())
        self.assertIn("Terms of Use", self.store.job(jid)["status_reason"])
        self.assertTrue(self.sup.held("openai"))
