"""Historical campaign: registry, seeding, grid, Grok ingestion, GPT triage, settlement, audit, passes, saturation,
publication to a draft PR (local origin, stand-in gh), the evidence gate and the note's offline verifier."""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from tests.base import Case, verdict
from triagent import broker, campaign, publish, schemas
from triagent.store import Store, canonical, now, sha256_bytes

A, B = "0x" + "a" * 40, "0x" + "b" * 40
TX = "0x" + "1" * 64
T = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SCORES = {k: 3 for k in schemas.SCORE_KEYS}


def decision(lead_id, kind="investigate", key="", **kw):
    return {"lead_id": lead_id, "decision": kind, "duplicate_of": "", "market": "0x" + "c" * 64,
            "event_time_utc": "2026-01-03T05:00:00Z", "hypothesis": "h", "innocent_explanations": ["public news"],
            "scores": SCORES, "novelty_key": key or f"campaign test {lead_id}", "task": "trace funding of " + A,
            "falsifier": "a comparator shows the same path", "reason": "checkable", **kw}


def grok_result(store, jid, leads):
    store.claim("grok", jid)
    store.save_result(jid, {"report": {"summary": "s", "leads": leads, "unresolved": [], "proposed_tests": []}})


def x_lead(pid, author="someone", addresses=(), claim="bet before strike"):
    return {"claim": claim, "post_url": f"https://x.com/{author}/status/{pid}", "post_id": str(pid),
            "posted_at": "2026-01-03T04:00:00Z", "addresses": list(addresses), "transactions": [], "first_hand": True,
            "proposed_onchain_check": "trace", "already_in_repo": False}


class Registry(Case):
    def test_seed_registers_known_cases_closed_and_open_leads_once(self):
        self.store.execute("INSERT INTO inventory(id,path,title,state,objective,conclusions,limits,sha256,scanned_at) "
                           "VALUES ('kpmg','research_notes/k/REPORT.md','KPMG','Done','','c','l','x',1)")
        notes = self.cfg.repo_dir / "research_notes" / "x-history-2026-11-06"
        (notes / "verification").mkdir(parents=True)
        (notes / "LEADS.csv").write_text(
            "lead_id,case,source,post_id,event_time_utc,candidate_proxy_or_destination,reported_claim,prior_overlap,"
            "source_status,priority,required_test\n"
            "L1,maduro,https://x.com/a/status/111111,111111,2026-01-03T00:00:00Z,,claim one,,X_REPORT_UNVERIFIED_CHAIN,1,t\n"
            f"L2,iran,https://x.com/b/status/222222,222222,,{A},claim two,,X_SCREENSHOT,2,t\n")
        (notes / "verification" / "LEADS_STATUS.csv").write_text(
            "lead_id,status,resolved_address,finding,test,report_section\nL2,REFUTED,,no,t,1\n")
        out = campaign.seed(self.cfg, self.store)
        self.assertEqual(out, {"known_cases": 1, "repo_leads": 2, "settled": 1})
        rows = {r["dedup_key"]: r for r in self.store.query("SELECT * FROM leads")}
        self.assertEqual(rows["case:inv:kpmg"]["state"], "closed")
        self.assertEqual(rows["x:111111"]["state"], "new")
        self.assertEqual(rows["x:222222"]["state"], "closed")
        self.assertIn("REFUTED", rows["x:222222"]["closure_reason"])
        self.assertEqual(campaign.seed(self.cfg, self.store), {"known_cases": 0, "repo_leads": 0, "settled": 0})
        self.assertEqual(len(Store(self.cfg.db_path).query("SELECT id FROM leads")), 3)  # survives a new connection

    def test_priority_is_bounded_and_cost_lowers_it(self):
        self.assertEqual(campaign.priority({k: 5 for k in schemas.SCORE_KEYS} | {"cost": 0}), 5)
        self.assertEqual(campaign.priority({k: 0 for k in schemas.SCORE_KEYS} | {"cost": 5}), 1)
        cheap = campaign.priority(SCORES | {"cost": 0})
        self.assertGreater(cheap, campaign.priority(SCORES | {"cost": 5}))

    def test_parse_utc(self):
        self.assertEqual(campaign.parse_utc("2026-01-03T05:00:00Z"), 1767416400)
        self.assertEqual(campaign.parse_utc("2026-01-03"), 1767398400)
        self.assertIsNone(campaign.parse_utc("soon"))


class Grid(Case):
    extra = {"ORCHESTRATOR": "n8n"}

    def test_one_cell_at_a_time_then_ingested_without_a_gpt_review(self):
        campaign.start(self.cfg, self.store)
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        jobs = self.store.jobs("origin='campaign' AND agent='grok'")
        self.assertEqual(len(jobs), 1)
        self.assertIn("pass 1, cell insider:2026", jobs[0]["task"])
        self.store.set_kv("campaign.tick", 0)
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        self.assertEqual(len(self.store.jobs("origin='campaign' AND agent='grok'")), 1)  # still one open cell
        grok_result(self.store, jobs[0]["id"], [x_lead(9001, addresses=[A]), x_lead(9001), x_lead(9002)])
        bro = broker.Broker(self.sup)
        choice, _ = bro.pick()
        self.assertTrue(choice is None or choice[1] != "review")  # a campaign cell is never audited as a mission
        self.store.set_kv("campaign.tick", 0)
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        self.assertEqual(self.store.job(jobs[0]["id"])["status"], "done")
        s = self.store.query("SELECT * FROM searches WHERE job_id=?", (jobs[0]["id"],))[0]
        self.assertEqual((s["posts"], s["new_leads"], s["duplicates"], s["outcome"]), (3, 2, 1, "positive"))
        lead = self.store.query("SELECT * FROM leads WHERE dedup_key='x:9001'")[0]
        self.assertEqual((lead["topic"], lead["period"], lead["state"]), ("insider", "2026", "new"))
        choice, _ = bro.pick()
        self.assertEqual(choice[:2], ("gpt", "triage"))
        self.assertEqual(len(self.store.jobs("origin='campaign' AND agent='grok'")), 2)  # next cell queued

    def test_failed_cell_counts_as_examined(self):
        campaign.start(self.cfg, self.store)
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        jid = self.store.jobs("origin='campaign'")[0]["id"]
        self.store.set_status(jid, "failed", "grok exit 1")
        self.store.set_kv("campaign.tick", 0)
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        self.assertEqual(self.store.query("SELECT outcome FROM searches WHERE job_id=?", (jid,))[0]["outcome"], "failed")
        self.assertEqual(campaign.next_cell(self.store, 1), "pre_announcement:2026")


class LiveIngest(Case):
    mode = "live"

    def test_unreadable_post_is_closed_and_overlap_flagged(self):
        self.store.execute("INSERT INTO known_addresses VALUES (?, 'research_notes/x/REPORT.md')", (A,))
        jid = campaign.enqueue_cell(self.store, 1, "wallets:2025")
        grok_result(self.store, jid, [x_lead(5001, addresses=[A]), x_lead(5002, author="fake")])
        fake = lambda leads: [{"post_id": "5001", "verified": True, "author": "someone", "created_at": "2026-01-03T04:00:00Z",
                               "time_matches": True, "text": "t"},
                              {"post_id": "5002", "verified": False, "author": "other", "created_at": None, "text": ""}]
        out = campaign.ingest_grok(self.cfg, self.store, self.store.job(jid), verify=fake)
        self.assertEqual(out["verified_posts"], 1)
        ok = self.store.query("SELECT * FROM leads WHERE dedup_key='x:5001'")[0]
        bad = self.store.query("SELECT * FROM leads WHERE dedup_key='x:5002'")[0]
        self.assertEqual(ok["state"], "new")
        self.assertIn("overlap with repository addresses", ok["checks"])
        self.assertEqual(bad["state"], "closed")
        self.assertIn("supervisor re-read", bad["closure_reason"])


class Triage(Case):
    def leads(self, n):
        return [campaign.add_lead(self.store, f"x:{700 + i}", "x_post", f"lead {i}")[0] for i in range(n)]

    def test_decisions_are_applied_once_and_omissions_deferred(self):
        l1, l2, l3, l4, l5 = self.leads(5)
        batch = self.store.query("SELECT * FROM leads ORDER BY id")
        out = {"decisions": [decision(l1), decision(l2, "duplicate", duplicate_of=l1), decision(l3, "close_noise"),
                             decision("L-forged"), decision(l1, "close_noise"), decision(l4, "x_followup", key="x follow l4")],
               "gaps": [{"title": "missing Base exits", "agent": "claude", "novelty_key": "campaign gap base exits",
                         "task": "trace Base exits", "falsifier": "f", "scores": SCORES, "reason": "gap"}],
               "notes": ""}
        res = campaign.apply_triage(self.cfg, self.store, batch, out, "campaign-triage-1")
        st = {r["id"]: r for r in self.store.query("SELECT * FROM leads")}
        self.assertEqual(st[l1]["state"], "investigating")
        job = self.store.job(st[l1]["job_id"])
        self.assertEqual((job["agent"], job["origin"], job["investigation"]), ("claude", "campaign", f"camp-{l1}"))
        self.assertIn("BEFORE the first bet", job["task"])
        self.assertEqual(st[l2]["state"], "duplicate")
        self.assertEqual(st[l3]["state"], "closed")
        self.assertEqual(st[l4]["owner"], "grok")
        self.assertEqual(st[l5]["state"], "deferred")  # omitted by GPT
        self.assertEqual(res["counts"]["omitted"], 1)
        self.assertEqual(res["gaps"], 1)
        self.assertEqual(st[l1]["event_ts"], 1767416400)
        # a second X follow-up of the same lead is refused (no loop)
        self.store.execute("UPDATE leads SET state='new' WHERE id=?", (l4,))
        lead4 = self.store.query("SELECT * FROM leads WHERE id=?", (l4,))
        campaign.apply_triage(self.cfg, self.store, lead4, {"decisions": [decision(l4, "x_followup", key="x follow again")],
                                                            "gaps": [], "notes": ""}, "campaign-triage-2")
        self.assertEqual(self.store.query("SELECT state FROM leads WHERE id=?", (l4,))[0]["state"], "deferred")

    def test_reused_novelty_key_closes_instead_of_duplicating_a_mission(self):
        l1, l2 = self.leads(2)
        batch = self.store.query("SELECT * FROM leads ORDER BY id")
        campaign.apply_triage(self.cfg, self.store, batch, {"decisions": [decision(l1, key="same key here"),
                                                                          decision(l2, key="same key here")],
                                                            "gaps": [], "notes": ""}, "t")
        self.assertEqual(len(self.store.jobs("origin='campaign'")), 1)
        self.assertIn("novelty key already used", self.store.query("SELECT closure_reason FROM leads WHERE id=?", (l2,))[0]
                      ["closure_reason"])

    def test_dry_run_triage_defers_without_a_provider(self):
        self.leads(3)
        self.assertEqual(campaign.triage(self.cfg, self.store, "w")["counts"], {"defer": 3})


class Settlement(Case):
    mode = "live"

    def investigating_lead(self):
        lid, _ = campaign.add_lead(self.store, "x:4242", "x_post", "strike bet", addresses_json=[A])
        batch = self.store.query("SELECT * FROM leads WHERE id=?", (lid,))
        campaign.apply_triage(self.cfg, self.store, batch, {"decisions": [decision(lid)], "gaps": [], "notes": ""}, "t")
        return lid, self.store.query("SELECT job_id FROM leads WHERE id=?", (lid,))[0]["job_id"]

    def finish(self, jid, claims, novelty=4, followups=()):
        self.store.claim("claude", jid)
        self.store.save_result(jid, {"report": {"summary": "s", "negative_results": [], "unresolved": [], "methods_used": [
            {"method": "timeline:first_trade", "version": "1", "window_start": 1767400000, "window_end": 0, "scope": "x",
             "outcome": "positive"}], "wallets_examined": [A]}})
        self.sup.apply_review(self.store.job(jid), json.loads(self.store.job(jid)["result_json"])["report"],
                              verdict(novelty=novelty, claims=claims, followups=followups), {})

    def test_supported_new_result_opens_an_audit_and_counts_for_the_pass(self):
        campaign.start(self.cfg, self.store)
        lid, jid = self.investigating_lead()
        self.finish(jid, [{"statement": "A paid B", "tier": "SUPPORTED", "evidence_ids": ["e" * 64], "objection": ""}])
        lead = self.store.query("SELECT * FROM leads WHERE id=?", (lid,))[0]
        self.assertEqual(lead["state"], "supported")
        self.assertEqual(lead["first_trade_ts"], 1767400000)
        self.assertEqual(self.store.query("SELECT state FROM publications")[0]["state"], "audit_pending")
        self.assertEqual(self.store.query("SELECT significant FROM passes WHERE n=1")[0]["significant"], 1)
        self.assertEqual(campaign.next_gpt_work(self.store)[0], "audit")

    def test_open_follow_up_keeps_the_lead_investigating_and_failure_settles_it(self):
        lid, jid = self.investigating_lead()
        follow = {"agent": "claude", "kind": "analysis", "novelty_key": "follow funding deeper", "task": "deeper",
                  "falsifier": "f", "expected_information_gain": 4, "est_cost_usd": 0.1}
        self.finish(jid, [{"statement": "x", "tier": "HYPOTHESIS", "evidence_ids": [], "objection": ""}], followups=[follow])
        self.assertEqual(self.store.query("SELECT state FROM leads WHERE id=?", (lid,))[0]["state"], "investigating")
        child = self.store.jobs("parent=?", (jid,))[0]
        self.store.set_status(child["id"], "failed", "max_turns")
        self.store.set_kv("campaign.state", "running")
        campaign.tick(self.cfg, self.sup, lambda *a, **k: True)
        self.assertEqual(self.store.query("SELECT state FROM leads WHERE id=?", (lid,))[0]["state"], "unresolved")
        self.assertFalse(self.store.query("SELECT 1 FROM publications"))


class Passes(Case):
    mode = "live"

    def test_two_empty_passes_saturate_and_notify_once(self):
        sent = []
        notifier = lambda title, message, link="": sent.append(message) or True
        campaign.start(self.cfg, self.store)
        for n in (1, 2):
            for cell in [f"{t}:{p}" for p in campaign.PERIODS for t in campaign.TOPICS]:
                self.store.execute("INSERT INTO searches(job_id,cell,topic,period,pass,created,finished,outcome) VALUES "
                                   "(?,?,?,?,?,?,?, 'negative')", (f"j{n}{cell}", cell, *cell.split(":"), n, now(), now()))
            self.assertTrue(campaign.pass_idle(self.store, n))
            self.assertEqual(campaign.close_pass(self.cfg, self.store, n, notifier), "pass 2" if n == 1 else "saturated")
        self.assertEqual(campaign.state(self.store), "saturated")
        self.assertEqual(sent, ["Campagne historique arrivée à saturation — bilan disponible"])
        campaign.tick(self.cfg, self.sup, notifier)
        self.assertEqual(len(sent), 1)
        report = (self.cfg.state_dir / "campaign" / "COVERAGE_REPORT.md").read_text()
        self.assertIn("does not mean every case of insider trading was found", report)
        self.assertEqual(campaign.start(self.cfg, self.store)["state"], "saturated")  # only reopen starts again

    def test_significant_pass_starts_another_and_requeues_deferred(self):
        campaign.start(self.cfg, self.store)
        lid, _ = campaign.add_lead(self.store, "x:1", "x_post", "d", state="deferred")
        self.store.execute("UPDATE passes SET significant=1 WHERE n=1")
        self.assertEqual(campaign.close_pass(self.cfg, self.store, 1, lambda *a, **k: True), "pass 2")
        self.assertEqual(self.store.query("SELECT state FROM leads WHERE id=?", (lid,))[0]["state"], "new")


def sh(cwd, *cmd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


class Publication(Case):
    mode = "live"

    def setUp(self):
        super().setUp()
        origin, seed = self.tmp / "origin.git", self.tmp / "seed"
        sh(self.tmp, "git", "init", "-q", "--bare", "-b", "main", str(origin))
        sh(self.tmp, "git", "init", "-q", "-b", "main", str(seed))
        for _, cmd in publish.CHECKS:
            (seed / cmd[0]).parent.mkdir(parents=True, exist_ok=True)
            (seed / cmd[0]).write_text("import sys\nsys.exit(0)\n")
        (seed / "README.md").write_text("accepted readme\n")
        sh(seed, "git", "add", "-A")
        sh(seed, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "main")
        sh(seed, "git", "push", "-q", str(origin), "main")
        self.origin, self.seed = origin, seed
        gh = self.tmp / "gh"
        gh.write_text("#!/bin/sh\necho \"$@\" >> \"$(dirname \"$0\")/gh.log\"\n"
                      "case \"$2\" in create) echo https://github.com/o/r/pull/77;; view) echo '{\"state\":\"OPEN\"}';; esac\n")
        gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
        self.cfg.values.update(PUBLISH_REMOTE=str(origin), GH_BIN=str(gh))
        self.prepare()

    def prepare(self):
        lid, _ = campaign.add_lead(self.store, "x:31337", "x_post", "strike bet", addresses_json=[A],
                                   sources_json=[{"url": "https://x.com/a/status/31337", "author": "a", "verified": True}],
                                   market="0x" + "c" * 64, first_trade_ts=1767400000, event_ts=1767416400)
        inv = f"camp-{lid}"
        self.store.ensure_investigation(inv, "t")
        self.store.execute("UPDATE leads SET investigation=?, state='supported' WHERE id=?", (inv, lid))
        jid = self.store.enqueue("claude", "analysis", "publish test mission", "task", origin="campaign", investigation=inv)
        ev = self.tmp / "ev"
        ev.mkdir()
        receipt = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"logs": [
            {"address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
             "topics": [T, "0x" + "0" * 24 + A[2:], "0x" + "0" * 24 + B[2:]], "data": "0x01"}]}}).encode()
        activity = json.dumps({"data": [{"proxy_wallet": A, "timestamp": 1767400000, "condition_id": "0x" + "c" * 64,
                                         "type": "TRADE", "side": "BUY", "size": 10, "usdc_size": 4.0, "price": 0.4,
                                         "transaction_hash": TX, "title": "Strike?", "outcome": "Yes",
                                         "name": "Real Name", "pseudonym": "Secret-Pseudo", "bio": "bio text"}]}).encode()
        self.rsha, self.asha = sha256_bytes(receipt), sha256_bytes(activity)
        (ev / f"{self.rsha}.raw").write_bytes(receipt)
        (ev / f"{self.asha}.raw").write_bytes(activity)
        self.store.add_evidence(self.rsha, "tg-fetch", f"polygon:eth_getTransactionReceipt:[\"{TX}\"]",
                                ev / f"{self.rsha}.raw", len(receipt), chain="polygon", job_id=jid)
        self.store.add_evidence(self.asha, "tg-fetch", f"https://data-api.polymarket.com/v2/activity?user={A}",
                                ev / f"{self.asha}.raw", len(activity), job_id=jid)
        self.store.add_edge(A, B, "DIRECT_TRANSFER", method="agent:t", level="receipt_verified", chain="polygon",
                            tx_hash=TX, amount="1", ts=1767401000, evidence_sha256=self.rsha, job_id=jid)
        self.store.execute("INSERT INTO publications(investigation,lead,branch,state,created,updated) VALUES "
                           "(?,?,?,'audit_pending',?,?)", (inv, lid, f"triagent/campaign-{lid.lower()}", now(), now()))
        audit = {"publishable": True, "reason": "new transfer", "title": "A paid B before the strike", "summary": "s",
                 "claims": [{"statement": "A paid B", "tier": "CONFIRMED", "evidence_ids": [self.rsha],
                             "verification_method": "receipt Transfer log"},
                            {"statement": "invented", "tier": "SUPPORTED", "evidence_ids": ["f" * 64],
                             "verification_method": "none"}],
                 "timeline": [{"time_utc": "2026-01-03T05:00:00Z", "event": "strike announced", "evidence_ids": []}],
                 "first_trade_time_utc": "", "event_time_utc": "", "innocent_explanations": ["news"],
                 "limits": ["one chain"], "not_demonstrated": ["identity"]}
        self.assertEqual(campaign.apply_audit(self.store, inv, audit), "prepared")
        self.inv, self.lid = inv, lid

    def test_draft_pr_after_all_checks_then_update_without_second_pr(self):
        kept = json.loads(self.store.query("SELECT audit_json FROM publications")[0]["audit_json"])
        self.assertEqual([c["statement"] for c in kept["kept_claims"]], ["A paid B"])  # unarchived evidence dropped
        self.assertEqual(publish.publish(self.cfg, self.store, self.inv), "draft_open")
        pub = self.store.query("SELECT * FROM publications")[0]
        self.assertEqual((pub["pr_number"], pub["state"]), (77, "draft_open"))
        branch = pub["branch"]
        files = subprocess.run(["git", "--git-dir", str(self.origin), "ls-tree", "-r", "--name-only", branch],
                               capture_output=True, text=True).stdout.split()
        note = f"{publish.NOTE_ROOT}/{self.lid}"
        self.assertIn(f"{note}/REPORT.md", files)
        self.assertIn(f"{note}/evidence/{self.rsha}.json", files)
        self.assertNotIn(f"{note}/evidence/{self.asha}.json", files)  # raw API pages are never copied
        main_readme = subprocess.run(["git", "--git-dir", str(self.origin), "show", f"{branch}:README.md"],
                                     capture_output=True, text=True).stdout
        self.assertEqual(main_readme, "accepted readme\n")
        positions = subprocess.run(["git", "--git-dir", str(self.origin), "show", f"{branch}:{note}/POSITIONS.csv"],
                                   capture_output=True, text=True).stdout
        self.assertIn("Strike?", positions)
        self.assertNotIn("Secret-Pseudo", positions)
        self.assertNotIn("Real Name", positions)
        self.assertEqual(json.loads(pub["checks_json"])[-1]["check"], "note_verify")
        self.assertTrue(all(c["code"] == 0 for c in json.loads(pub["checks_json"])))
        self.assertEqual(publish.publish(self.cfg, self.store, self.inv), "unchanged")
        log = (self.tmp / "gh.log").read_text()
        self.assertEqual(log.count("pr create --draft --base main"), 1)
        self.assertNotIn("merge", log)

    def test_a_failing_check_stops_before_any_push(self):
        (self.seed / "scripts/test_phi.py").write_text("import sys\nprint('broken')\nsys.exit(1)\n")
        sh(self.seed, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "break")
        sh(self.seed, "git", "push", "-q", str(self.origin), "main")
        self.assertEqual(publish.publish(self.cfg, self.store, self.inv), "tests_failed")
        pub = self.store.query("SELECT * FROM publications")[0]
        self.assertIn("test_phi", pub["reason"])
        heads = subprocess.run(["git", "--git-dir", str(self.origin), "branch", "--list"], capture_output=True, text=True).stdout
        self.assertNotIn("triagent/campaign", heads)
        self.assertFalse((self.tmp / "gh.log").exists())
        sent = []
        self.store.set_kv("campaign.state", "running")
        for _ in range(2):  # the owner is told once, not at every tick
            self.store.set_kv("campaign.tick", 0)
            campaign.tick(self.cfg, self.sup, lambda t, m, link="": sent.append(m) or True)
        self.assertEqual(len(sent), 1)
        self.assertIn("test_phi", sent[0])

    def test_secret_in_content_refuses(self):
        self.secrets(UI_TOKEN="topsecretvalue123")
        self.cfg.values.update(PUBLISH_REMOTE=str(self.origin), GH_BIN=str(self.tmp / "gh"))
        self.store.execute("UPDATE leads SET title='leak topsecretvalue123' WHERE id=?", (self.lid,))
        audit = json.loads(self.store.query("SELECT audit_json FROM publications")[0]["audit_json"])
        audit["title"] = ""
        self.store.execute("UPDATE publications SET audit_json=?", (canonical(audit),))
        self.assertEqual(publish.publish(self.cfg, self.store, self.inv), "refused")

    def test_foreign_branch_is_refused(self):
        self.store.execute("UPDATE publications SET branch='main'")
        self.assertEqual(publish.publish(self.cfg, self.store, self.inv), "refused")

    def test_note_verifier_catches_tampered_evidence(self):
        files = publish.build_note(self.cfg, self.store, self.inv)
        note = self.tmp / "note"
        for name, raw in files.items():
            (note / name).parent.mkdir(parents=True, exist_ok=True)
            (note / name).write_bytes(raw)
        run = lambda: subprocess.run([sys.executable, "-I", str(note / "verify.py")], capture_output=True, text=True,
                                     env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(run().returncode, 0, run().stdout)
        timeline = (note / "TIMELINE.csv").read_text()
        self.assertIn(",B,", timeline)  # the transfer sits between the first bet and the event
        self.assertIn(",C,", timeline)  # the announcement itself is phase C
        p = note / "evidence" / f"{self.rsha}.json"
        p.write_bytes(p.read_bytes().replace(b"0x01", b"0x02"))
        self.assertEqual(run().returncode, 1)
