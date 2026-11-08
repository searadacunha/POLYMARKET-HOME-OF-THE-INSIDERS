"""GROK_MODE=grok_cli against a stand-in `grok` binary that prints the output shape of grok 1.0.77 measured on
2026-11-08 (structuredOutput = consecutive JSON objects), and the supervisor's re-reading of cited X posts."""
import json
import stat

from tests.base import Case
from triagent import providers
from triagent.util import ProviderError

FAKE = """#!/bin/sh
dir=$(dirname "$0")
printf '%s\\n' "$@" > "$dir/args"
env > "$dir/env"
cat "$dir/out.json"
"""
FIRST = {"summary": "searching", "leads": [], "unresolved": [], "proposed_tests": []}
FINAL = {"summary": "two posts", "leads": [{"claim": "price note", "post_url": "https://x.com/Polymarket/status/2007568167552393432",
                                           "post_id": "2007568167552393432", "posted_at": "2026-01-03T21:42:04Z",
                                           "addresses": [], "transactions": [], "first_hand": True,
                                           "proposed_onchain_check": "none", "already_in_repo": False}],
         "unresolved": [], "proposed_tests": []}


class GrokCliTests(Case):
    mode = "live"

    def setUp(self):
        self.extra = {"GROK_MODE": "grok_cli"}
        super().setUp()
        self.bin = self.tmp / "fakebin"
        self.bin.mkdir()
        exe = self.bin / "grok"
        exe.write_text(FAKE)
        exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
        (self.bin / "out.json").write_text(json.dumps({
            "structuredOutput": json.dumps(FIRST) + json.dumps(FINAL), "text": "prose", "total_cost_usd": 0.148,
            "sessionId": "90c79809", "requestId": "req-1", "num_turns": 4, "usage": {"output_tokens": 8151}}))
        self.cfg.values["GROK_BIN"] = str(exe)
        (self.cfg.state_dir / "grok-home").mkdir()
        (self.cfg.state_dir / "grok-home" / "auth.json").write_text("{}")
        self.jid = self.store.enqueue("grok", "x_research", "x posts before the move 2026", "find posts", origin="seed")

    def test_last_structured_object_is_kept_and_the_session_is_locked_down(self):
        _, (report, usd, meta) = providers.grok_run(self.cfg, self.store, self.store.claim("grok"))
        self.assertEqual(report["summary"], "two posts")
        self.assertEqual((usd, meta["request_id"], meta["num_turns"]), (0.148, "req-1", 4))
        args = (self.bin / "args").read_text().splitlines()
        self.assertEqual(args[args.index("--tools") + 1], "web_search,web_fetch")
        self.assertEqual(args[args.index("--permission-mode") + 1], "dontAsk")
        self.assertIn("use_tool", args)
        self.assertNotIn("run_terminal_command", " ".join(args))
        env = dict(line.split("=", 1) for line in (self.bin / "env").read_text().splitlines() if "=" in line)
        self.assertEqual(env["HOME"], str(self.cfg.state_dir / "grok-empty-home"))  # no ~/.claude, no ~/.grok
        self.assertEqual(env["GROK_HOME"], str(self.cfg.state_dir / "grok-home"))
        self.assertEqual(list((self.cfg.state_dir / "grok-empty-home").iterdir()), [])

    def test_missing_grok_login_is_an_auth_error(self):
        (self.cfg.state_dir / "grok-home" / "auth.json").unlink()
        with self.assertRaises(ProviderError) as e:
            providers.grok_run(self.cfg, self.store, self.store.claim("grok"))
        self.assertEqual(e.exception.kind, "auth")

    def test_cited_posts_are_reread_by_the_supervisor(self):
        real = {"user": {"screen_name": "Polymarket"}, "created_at": "2026-01-03T21:42:04.000Z", "text": "..."}
        leads = FINAL["leads"] + [{"post_url": "https://x.com/someone/status/2007568167552393432"},
                                  {"post_url": "https://example.com/not-a-post"}]
        out = providers.verify_x_leads(leads, fetch=lambda url, **kw: real)
        self.assertEqual([(o["verified"], o.get("time_matches")) for o in out], [(True, True), (False, False), (False, None)])

        def down(url, **kw):
            raise ProviderError("transient", "HTTP 504")
        self.assertIsNone(providers.verify_x_leads(FINAL["leads"], fetch=down)[0]["verified"])  # unknown, not verified

    def test_last_object_survives_a_truncated_tail(self):
        self.assertEqual(providers.last_object(json.dumps(FIRST) + json.dumps(FINAL) + '{"summary": "cut'), FINAL)
        self.assertIsNone(providers.last_object(""))
