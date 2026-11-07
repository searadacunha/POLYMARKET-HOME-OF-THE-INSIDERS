"""Full research cycle with simulated providers: Claude -> OpenAI -> Grok -> OpenAI -> Claude."""
import json
from pathlib import Path
from unittest.mock import patch

from tests.base import Case, followup, verdict


class CycleTests(Case):
    def test_claude_openai_grok_openai_claude_chain(self):
        root = self.store.enqueue("claude", "analysis", "seed funding replay 2026", "Replay funding of X",
                                  origin="seed")
        script = iter([
            verdict(4, followups=[followup("grok", "x posts before the move 2026")]),
            verdict(4, followups=[followup("claude", "replay the lead from x 2026")]),
            verdict(0, decision="stop_no_new_information"),
        ])
        with patch("triagent.providers.review", side_effect=lambda *a, **k: next(script)):
            self.sup.tick_claude()                       # Claude mission A
            self.assertEqual(self.store.job(root)["status"], "reviewing")
            self.sup.tick_review()                       # OpenAI reviews A, sends Grok
            self.assertEqual(self.store.job(root)["status"], "done")
            grok = self.store.jobs("agent='grok'")[0]
            self.assertEqual((grok["parent"], grok["depth"], grok["kind"]), (root, 1, "x_research"))
            self.sup.tick_grok()                         # Grok mission B
            self.assertEqual(self.store.job(grok["id"])["status"], "reviewing")
            self.sup.tick_review()                       # OpenAI reviews B, sends Claude
            child = self.store.jobs("agent='claude' AND parent=?", (grok["id"],))[0]
            self.sup.tick_claude()                       # Claude mission C, fresh session
            self.sup.tick_review()                       # no novelty: investigation stops
        a, c = self.store.job(root), self.store.job(child["id"])
        self.assertEqual(c["status"], "done")
        self.assertNotEqual(a["session_id"], c["session_id"])
        mission = (Path(c["mission_dir"]) / "MISSION.md").read_text()
        self.assertIn(f"context/{root}.json", mission)
        self.assertIn(f"context/{grok['id']}.json", mission)
        ctx = json.loads((Path(c["mission_dir"]) / "context" / f"{root}.json").read_text())
        self.assertEqual(ctx["result_sha256"], a["result_sha256"])
        inv = self.store.investigation(a["investigation"])
        self.assertEqual(inv["status"], "exhausted")
        self.assertIsNone(self.store.enqueue("claude", "analysis", "one more idea 2026", "more", origin="review",
                                             investigation=inv["id"], parent=child["id"], depth=3))

    def test_low_novelty_produces_no_followup(self):
        jid = self.store.enqueue("claude", "analysis", "a repeated study 2026", "Repeat", origin="seed")
        with patch("triagent.providers.review",
                   return_value=verdict(2, followups=[followup("claude", "never queued 2026")])):
            self.sup.tick_claude()
            self.sup.tick_review()
        self.assertEqual(self.store.job(jid)["status"], "done")
        self.assertEqual(len(self.store.jobs("1=1")), 1)

    def test_depth_and_children_are_bounded(self):
        jid = self.store.enqueue("claude", "analysis", "deep chain root 2026", "Root", origin="seed")
        many = [followup("claude", f"child number {i} 2026") for i in range(5)]
        with patch("triagent.providers.review", return_value=verdict(5, followups=many)):
            self.sup.tick_claude()
            self.sup.tick_review()
        self.assertEqual(len(self.store.jobs("parent=?", (jid,))), self.cfg.int("MAX_CHILDREN"))
        self.assertIsNone(self.store.enqueue("claude", "analysis", "too deep 2026", "x", origin="review",
                                             depth=self.cfg.int("MAX_DEPTH") + 1))
