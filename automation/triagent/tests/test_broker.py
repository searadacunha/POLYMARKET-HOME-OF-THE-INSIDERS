"""n8n broker contract (n8n/TRIAGENT_N8N_ADAPTIVE_V2.json): idempotent ingest, single-use atomic leases,
asynchronous dispatch, local-only reconcile, durations, early alerts, event sender, HTTP security."""
import json
import socket
import stat
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tests.base import Case, followup, verdict
from triagent import broker, polymarket, providers
from triagent.service import Supervisor
from triagent.store import EVENT_TYPES, now
from triagent.util import ProviderError, http

WORKFLOW = Path(__file__).resolve().parents[1] / "n8n" / "TRIAGENT_N8N_ADAPTIVE_V2.json"


class BrokerCase(Case):
    extra = {"ORCHESTRATOR": "n8n"}

    def setUp(self):
        super().setUp()
        self.secrets(BROKER_TOKEN="b" * 32, N8N_WAKE_TOKEN="w" * 32)
        self.bro = broker.Broker(self.sup)
        self.notified = []
        self.bro.notifier = lambda title, msg, **_: self.notified.append((title, msg)) or True

    def lease_dispatch(self):
        lease = self.bro.lease({})[1]
        self.assertTrue(lease["ready"], lease)
        code, out = self.bro.dispatch({"job_id": lease["job_id"], "lease_id": lease["lease_id"],
                                       "agent": lease["agent"], "fresh_session": True, "async_launch": True})
        self.assertEqual(code, 202, out)
        return lease

    def wait_threads(self):
        for t in list(self.bro.inflight.values()):
            t.join(10)


class EventAndLeaseTests(BrokerCase):
    def test_ingest_is_idempotent_and_validated(self):
        ev = self.store.emit("work.ready", job_id="abc")
        first = self.bro.ingest({"event_id": ev, "event_type": "work.ready"})[1]
        again = self.bro.ingest({"event_id": ev, "event_type": "work.ready"})[1]
        self.assertEqual((first["duplicate"], again["duplicate"], again["alert_ready"]), (False, True, False))
        self.assertEqual(self.bro.ingest({"event_id": ev, "event_type": "rm -rf"})[0], 400)
        self.assertEqual(self.bro.ingest({"event_id": "x;", "event_type": "work.ready"})[0], 400)
        self.assertEqual(self.bro.ingest({"event_id": "manual-test-0001", "event_type": "work.ready"})[0], 200)
        self.assertIs(self.bro.ingest({"event_id": "manual-test-0001", "event_type": "work.ready"})[1]["duplicate"], True)

    def test_concurrent_wakes_start_one_job(self):
        self.store.enqueue("claude", "analysis", "only once please 2026", "task", origin="seed")
        results = []
        threads = [threading.Thread(target=lambda: results.append(self.bro.lease({})[1])) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sum(r["ready"] for r in results), 1)
        self.assertEqual(self.store.query("SELECT count(*) n FROM leases")[0]["n"], 1)

    def test_lease_is_single_use_expires_and_must_match(self):
        self.store.enqueue("claude", "analysis", "single use lease 2026", "task", origin="seed")
        lease = self.bro.lease({})[1]
        body = {"job_id": lease["job_id"], "lease_id": lease["lease_id"], "agent": "gpt"}
        self.assertEqual(self.bro.dispatch(body)[0], 409)  # wrong agent: lease burnt
        self.assertEqual(self.bro.dispatch(body | {"agent": "claude"})[0], 409)
        lease = self.bro.lease({})[1]
        with patch("time.time", return_value=time.time() + 3600):
            self.assertEqual(self.bro.dispatch({"job_id": lease["job_id"], "lease_id": lease["lease_id"],
                                                "agent": "claude"})[1]["error"], "lease expired")
        lease = self.lease_dispatch()
        self.assertEqual(self.bro.dispatch({"job_id": lease["job_id"], "lease_id": lease["lease_id"],
                                            "agent": "claude"})[0], 409)  # second use
        self.assertEqual(self.store.job(lease["job_id"])["attempts"], 1)

    def test_full_chain_through_leases_claude_gpt_grok_gpt_claude(self):
        root = self.store.enqueue("claude", "analysis", "seed chain via broker 2026", "Replay", origin="seed")
        script = iter([verdict(4, followups=[followup("grok", "x posts before move 2026")]),
                       verdict(4, followups=[followup("claude", "replay the x lead 2026")]),
                       verdict(0, decision="stop_no_new_information")])
        order = []
        with patch("triagent.providers.review", side_effect=lambda *a, **k: next(script)):
            for _ in range(6):
                lease = self.lease_dispatch()
                order.append(lease["agent"])
                self.wait_threads()
        self.assertEqual(order, ["claude", "gpt", "grok", "gpt", "claude", "gpt"])
        self.assertFalse(self.bro.lease({})[1]["ready"])  # no novelty: nothing left, nothing invented
        jobs = self.store.jobs("1=1")
        self.assertTrue(all(j["status"] == "done" for j in jobs))
        self.assertEqual(len({j["session_id"] for j in jobs if j["agent"] == "claude"}), 2)
        self.assertEqual(self.store.job(root)["attempts"], 1)
        types = {r["event_type"] for r in self.store.query("SELECT event_type FROM bus")}
        self.assertTrue({"work.ready", "mission.completed"} <= types)

    def test_gpt_review_answers_202_before_the_review_ends(self):
        self.store.enqueue("claude", "analysis", "slow review 2026", "task", origin="seed")
        self.lease_dispatch()
        release = threading.Event()

        def slow_review(*a, **k):
            release.wait(5)
            return verdict(0, decision="stop_no_new_information")
        with patch("triagent.providers.review", side_effect=slow_review):
            start = time.monotonic()
            lease = self.lease_dispatch()
            self.assertLess(time.monotonic() - start, 1)
            self.assertEqual(lease["agent"], "gpt")
            self.assertEqual(self.store.job(lease["job_id"])["status"], "reviewing")
            self.assertFalse(self.bro.lease({})[1]["ready"])  # the GPT slot is busy
            release.set()
            self.wait_threads()
        self.assertEqual(self.store.job(lease["job_id"])["status"], "done")
        self.assertEqual(self.store.query("SELECT state FROM leases WHERE lease_id=?", (lease["lease_id"],))[0]["state"],
                         "finished")

    def test_reject_blocks_instead_of_dropping(self):
        jid = self.store.enqueue("claude", "analysis", "rejected job 2026", "task", origin="seed")
        lease = self.bro.lease({})[1]
        self.assertEqual(self.bro.reject({"job_id": jid, "lease_id": lease["lease_id"], "reason": "unsupported_agent"})[0], 200)
        self.assertEqual(self.store.job(jid)["status"], "blocked")


    def test_two_concurrent_collections_store_one_result(self):
        jid = self.store.enqueue("claude", "analysis", "finished while polled twice 2026", "task", origin="seed")
        job = self.store.claim("claude")
        mdir = self.tmp / "m"
        mdir.mkdir()
        (mdir / "claude_output.json").write_text(json.dumps(providers.fake_claude_output(job)))
        self.store.set_status(jid, "running", "x", mission_dir=str(mdir))
        threads = [threading.Thread(target=f) for f in (self.sup.poll_claude, lambda: self.bro.reconcile({})) * 2]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(self.store.query("SELECT count(*) n FROM costs WHERE job_id=?", (jid,))[0]["n"], 1)
        self.assertEqual(self.store.query("SELECT count(*) n FROM bus WHERE event_type='mission.completed'")[0]["n"], 1)


class GateTests(BrokerCase):
    mode = "live"

    def test_unavailable_grok_held_claude_budget_and_disk(self):
        self.cfg.values.update(CLAUDE_BIN="/nonexistent/claude", GROK_MODE="xai_api")
        self.store.enqueue("grok", "x_research", "grok without key 2026", "task", origin="seed")
        self.store.enqueue("claude", "analysis", "claude without binary 2026", "task", origin="seed")
        self.store.set_kv("last_plan", now())
        reasons = self.bro.lease({})[1]["reasons"]
        self.assertIn("NOT available", reasons["grok"])
        self.assertIn("binary", reasons["claude"])
        self.sup.hold("openai", 600, "auth: expired")
        self.assertIn("on hold", self.bro.lease({})[1]["reasons"]["gpt"])
        self.cfg.values["DISK_MIN_FREE_GB"] = "100000"
        self.assertIn("disk", self.bro.lease({})[1]["reasons"]["gate"])

    def test_daily_cap_blocks_claude(self):
        fake = self.tmp / "claude"
        fake.write_text("#!/bin/sh\n")
        self.cfg.values.update(CLAUDE_BIN=str(fake), CLAUDE_MAX_MISSIONS_DAY="0")
        self.store.enqueue("claude", "analysis", "over the cap 2026", "task", origin="seed")
        self.store.set_kv("last_plan", now())
        self.assertIn("cap", self.bro.lease({})[1]["reasons"]["claude"])


class LongMissionTests(BrokerCase):
    """A real child process stands in for Claude Code; the clock is moved, never the process."""
    mode = "live"

    def setUp(self):
        super().setUp()
        fake = self.tmp / "bin" / "claude"
        fake.parent.mkdir()
        fake.write_text("#!/bin/sh\nexec sleep 120\n")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.cfg.values.update(CLAUDE_BIN=str(fake), CLAUDE_TIMEOUT_S="7200", STALL_AFTER_S="1200")
        self.store.set_kv("last_plan", now())  # no periodic plan in these tests
        self.jid = self.store.enqueue("claude", "analysis", "long mission 2026", "task", origin="seed")

    def tearDown(self):
        job = self.store.job(self.jid)
        providers.kill_group(job and job["pid"])
        for proc in self.sup.procs.values():
            proc.wait(10)
        super().tearDown()

    def test_dispatch_returns_at_once_and_long_missions_are_never_relaunched(self):
        start = time.monotonic()
        with patch("triagent.providers.review", side_effect=AssertionError("no model call")), \
                patch("triagent.providers.plan", side_effect=AssertionError("no model call")):
            self.lease_dispatch()
            self.assertLess(time.monotonic() - start, 2)
            pid = self.store.job(self.jid)["pid"]
            t0 = time.time()
            for minutes in (5, 20, 90):
                with patch("time.time", return_value=t0 + minutes * 60):
                    out = self.bro.reconcile({"source": "watchdog", "external_calls": False})[1]
                    self.assertFalse(self.bro.lease({})[1]["ready"])
                self.assertFalse(out["external_calls"])
                job = self.store.job(self.jid)
                self.assertEqual((job["status"], job["attempts"], job["pid"]), ("running", 1, pid))
                self.assertEqual(out["running"][0]["suspected_stalled"], minutes > 20)
            self.assertTrue(self.store.job(self.jid)["status_reason"].startswith("suspected_stalled"))
            self.assertTrue(providers.pid_alive(pid, "claude"))  # a late mission is labelled, not killed
            self.assertEqual(self.store.query("SELECT count(*) n FROM leases")[0]["n"], 1)
            with patch("time.time", return_value=t0 + 7300):  # only the explicit hard budget stops it
                self.bro.reconcile({})
            self.assertEqual(self.store.job(self.jid)["status"], "failed")

    def test_restart_adopts_the_running_process(self):
        self.lease_dispatch()
        pid = self.store.job(self.jid)["pid"]
        sup = Supervisor(self.cfg, self.store)  # supervisor restarted while the mission runs
        sup.recover()
        bro = broker.Broker(sup)
        bro.recover()
        bro.reconcile({})
        job = self.store.job(self.jid)
        self.assertEqual((job["status"], job["attempts"], job["pid"]), ("running", 1, pid))
        self.assertEqual(self.store.query("SELECT state FROM leases")[0]["state"], "dispatched")
        self.assertIn("running", bro.lease({})[1]["reasons"]["claude"])


class DurationTests(BrokerCase):
    def test_percentiles_need_enough_observed_runs(self):
        for i, secs in enumerate([60, 70, 80]):
            self.store.run_start("claude_code", "analysis", f"j{i}", mode="subscription")
            self.store.execute("UPDATE runs SET finished_at=started_at+?, runtime_sec=?, exit_status='ok' WHERE "
                               "work_id=?", (secs, secs, f"j{i}"))
        self.store.run_start("codex_cli", "review", "dry", mode="dryrun")
        self.store.run_end("dry", "ok")
        est = broker.estimates(self.store, self.cfg)
        self.assertEqual(len(est), 1)  # dry runs never count
        self.assertIsNone(est[0]["p50_s"])
        self.assertIn("insufficient", est[0]["confidence"])
        for i, secs in enumerate([100, 110, 120, 130, 140, 300, 1000]):
            self.store.run_start("claude_code", "analysis", f"k{i}", mode="subscription")
            self.store.execute("UPDATE runs SET runtime_sec=?, exit_status='ok' WHERE work_id=?", (secs, f"k{i}"))
        est = broker.estimates(self.store, self.cfg)[0]
        self.assertEqual((est["n"], est["p50_s"], est["p90_s"], est["p99_s"]), (10, 110, 300, None))


class AlertTests(BrokerCase):
    mode = "live"

    def alert(self, address="0x" + "a" * 40, cid="0xc1", score=4):
        self.store.execute("""INSERT INTO alerts(created,address,condition_id,trade_ts,usdc,score,flags_json,
                              features_json,level) VALUES (?,?,?,?,?,?,?,?,?)""",
                           (now(), address, cid + "0" * 62, now() - 60, 20000, score,
                            json.dumps(["NEW_WALLET", "FRESH_FUNDING", "FEW_PRIOR_TRADES", "CONCENTRATED"][:score]),
                            json.dumps({"features": {"n_trades_before": 0}, "funders": []}), "WATCH"))
        aid = self.store.query("SELECT max(id) n FROM alerts")[0]["n"]
        return str(aid), self.store.emit("alert.early", alert_id=str(aid))

    def test_notified_once_with_dossier_and_cooldown(self):
        aid, ev = self.alert()
        first = self.bro.ingest({"event_id": ev, "event_type": "alert.early"})[1]
        self.assertIs(first["alert_ready"], True)
        out = self.bro.notify({"event_id": ev, "alert_id": aid, "channel": "macos", "one_time": True})[1]
        self.assertTrue(out["sent"])
        dossier = Path(out["dossier"]).read_text()
        self.assertIn("NOT VERIFIED", dossier)
        self.assertIn("not evidence of insider trading", dossier)
        self.assertEqual(self.bro.notify({"alert_id": aid})[1]["reason"], "already notified")
        self.assertIs(self.bro.ingest({"event_id": ev, "event_type": "alert.early"})[1]["alert_ready"], False)
        other, _ = self.alert(cid="0xc2")
        self.assertEqual(self.bro.notify({"alert_id": other})[1]["reason"], "cooldown for this account")
        low, _ = self.alert(address="0x" + "c" * 40, cid="0xc3", score=3)
        self.assertIn("ALERT_NOTIFY_MIN_FLAGS", self.bro.notify({"alert_id": low})[1]["reason"])
        self.assertEqual(len(self.notified), 1)
        self.assertIn("NOT VERIFIED", self.notified[0][0])

    def test_later_withdrawal_never_enters_a_pre_trade_alert(self):
        t, wallet, tx = now() - 3600, "0x" + "a" * 40, "0x" + "b" * 64
        later = "0x" + "e" * 64
        self.store.execute("""INSERT INTO trades(tx_hash,proxy_wallet,condition_id,token_id,side,size,price,usdc,ts,
                              title,outcome,seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (tx, wallet, "0xc1", "1", "BUY", 40000, 0.5, 20000, t, "Market", "Yes", now()))
        activity = {"data": [
            {"type": "DEPOSIT", "timestamp": t - 7200, "usdc_size": 20000, "transaction_hash": "0x" + "d" * 64},
            {"type": "TRADE", "timestamp": t, "usdc_size": 20000, "condition_id": "0xc1", "transaction_hash": tx},
            {"type": "WITHDRAWAL", "timestamp": t + 600, "usdc_size": 30000, "transaction_hash": later}],
            "pagination": {"next_cursor": None}}
        asked = []

        def post(url, method="POST", body=None, **kw):
            asked.append(body["params"][0] if body["params"] else body["method"])
            result = hex(10**6) if body["method"] == "eth_blockNumber" else (
                {"status": "0x1", "blockNumber": hex(100), "logs": []} if body["params"][0] == tx else None)
            return 200, json.dumps({"jsonrpc": "2.0", "id": 1, "result": result}).encode()
        polymarket.scan(self.cfg, self.store, fetch=lambda url: activity if "activity" in url else [], post=post)
        self.assertNotIn(later, asked)  # the cash-out after the trade is not even fetched
        alert = self.store.query("SELECT * FROM alerts")[0]
        self.assertNotIn("SHARED_DESTINATION", alert["flags_json"])
        self.assertEqual(json.loads(alert["features_json"])["destinations"], [])
        self.assertEqual(self.store.query("SELECT count(*) n FROM bus WHERE event_type='alert.early'")[0]["n"], 1)


    def test_alert_is_notified_without_n8n_and_once_when_n8n_is_down(self):
        self.cfg.values["ORCHESTRATOR"] = "internal"
        bro = broker.Broker(Supervisor(self.cfg, self.store))
        bro.notifier = self.bro.notifier
        aid, _ = self.alert()
        bro.send_pending()
        bro.send_pending()
        self.assertEqual(len(self.notified), 1)
        self.assertTrue(self.store.query("SELECT notified_at FROM alerts WHERE id=?", (int(aid),))[0]["notified_at"])
        other, ev = self.alert(address="0x" + "d" * 40, cid="0xc4")

        def down(url, **kw):
            raise ProviderError("transient", "connection refused")
        for _ in range(3):
            self.store.execute("UPDATE bus SET next_try=0")
            self.bro.send_pending(post=down)
        self.assertEqual(len(self.notified), 1)  # not yet: n8n may only be restarting
        self.store.execute("UPDATE bus SET next_try=0")
        self.bro.send_pending(post=down)
        self.bro.send_pending(post=down)
        self.assertEqual(len(self.notified), 2)
        self.assertEqual(self.bro.notify({"alert_id": other})[1]["reason"], "already notified")  # n8n back later


class DryRunAlertTests(BrokerCase):
    def test_a_simulation_never_notifies(self):
        self.store.execute("""INSERT INTO alerts(created,address,condition_id,trade_ts,usdc,score,flags_json,
                              features_json) VALUES (?,?,?,?,?,?,?,?)""",
                           (now(), "0x" + "a" * 40, "0xc1", now(), 9e5, 9, "[]", "{}"))
        self.assertIn("dry run", self.bro.notify({"alert_id": "1"})[1]["reason"])
        self.assertEqual(self.notified, [])


class SenderTests(BrokerCase):
    def test_events_are_posted_once_with_header_and_backoff(self):
        posts = []
        self.store.emit("work.ready", job_id="j1")
        ok = lambda url, **kw: posts.append(kw) or (200, b"{}")  # noqa: E731
        self.assertEqual(self.bro.send_pending(post=ok), 1)
        self.assertEqual(self.bro.send_pending(post=ok), 0)
        self.assertEqual(posts[0]["headers"], {"X-TriAgent-Wake": "w" * 32})
        self.assertEqual(posts[0]["body"]["event_type"], "work.ready")

        def down(url, **kw):
            raise ProviderError("transient", "connection refused")
        self.store.emit("mission.completed", job_id="j2")
        self.assertEqual(self.bro.send_pending(post=down), 0)
        row = self.store.query("SELECT * FROM bus WHERE job_id='j2'")[0]
        self.assertEqual((row["sent_at"], row["send_attempts"]), (None, 1))
        self.assertGreater(row["next_try"], now())

    def test_internal_orchestrator_routes_nothing(self):
        self.cfg.values["ORCHESTRATOR"] = "internal"
        sup = Supervisor(self.cfg, self.store)
        self.store.emit("work.ready", job_id="j1")
        bro = broker.Broker(sup)
        self.assertEqual(bro.send_pending(post=lambda *a, **k: self.fail("posted")), 0)
        self.assertEqual(self.store.query("SELECT sent_at FROM bus")[0]["sent_at"], 0)
        self.store.enqueue("claude", "analysis", "internal scheduler owns it 2026", "task", origin="seed")
        self.assertIn("internal", bro.lease({})[1]["reasons"]["orchestrator"])  # never two schedulers


class HttpTests(BrokerCase):
    def test_loopback_header_auth_and_limits(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.cfg.values["BROKER_PORT"] = str(port)
        server = ThreadingHTTPServer(("127.0.0.1", port), broker.make_handler(self.bro))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{port}/v1/work/lease"
        try:
            with self.assertRaises(ProviderError) as e:
                http(url, method="POST", body={})
            self.assertEqual(e.exception.status, 401)
            with self.assertRaises(ProviderError) as e:
                http(url, method="POST", body={}, headers={"X-TriAgent-Key": "b" * 31 + "c"})
            self.assertEqual(e.exception.status, 401)
            with self.assertRaises(ProviderError) as e:
                http(url, method="POST", body={}, headers={"X-TriAgent-Key": "b" * 32, "Host": "evil.example"})
            self.assertEqual(e.exception.status, 403)
            with self.assertRaises(ProviderError) as e:
                http(url, method="POST", body={"x": "y" * 70000}, headers={"X-TriAgent-Key": "b" * 32})
            self.assertEqual(e.exception.status, 413)
            code, raw = http(url, method="POST", body={}, headers={"X-TriAgent-Key": "b" * 32})
            self.assertEqual((code, json.loads(raw)["ready"]), (200, False))
        finally:
            server.shutdown()
            server.server_close()


class WorkflowContractTests(BrokerCase):
    def test_every_n8n_call_is_served_and_safe(self):
        wf = json.loads(WORKFLOW.read_text())
        self.assertIs(wf["active"], False)
        nodes = {n["name"]: n for n in wf["nodes"]}
        types = {n["type"] for n in wf["nodes"]}
        self.assertFalse(types & {"n8n-nodes-base.executeCommand", "n8n-nodes-base.ssh"})
        hooks = [n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.webhook"]
        self.assertEqual([(h["parameters"]["path"], h["parameters"]["authentication"]) for h in hooks],
                         [("triagent-v2-wake", "headerAuth")])
        self.assertEqual(self.cfg.get("N8N_WAKE_URL"), "http://127.0.0.1:5678/webhook/triagent-v2-wake")
        for n in wf["nodes"]:
            if n["type"] == "n8n-nodes-base.httpRequest":
                p = n["parameters"]
                self.assertTrue(p["url"].startswith("http://127.0.0.1:8791/"), n["name"])
                self.assertIn(p["url"][len("http://127.0.0.1:8791"):], broker.ROUTES)
                self.assertEqual((p["method"], p["genericAuthType"]), ("POST", "httpHeaderAuth"))
        code = nodes["Validate event envelope"]["parameters"]["jsCode"]
        self.assertEqual(set(json.loads(code.split("const allowed = ")[1].split(";")[0].replace("'", '"'))),
                         set(EVENT_TYPES))
        timer = nodes["Recovery every 15 min"]["parameters"]["rule"]["interval"][0]
        self.assertEqual((timer["field"], timer["minutesInterval"]), ("minutes", 15))
        self.assertEqual(wf["connections"]["Recovery every 15 min"]["main"][0][0]["node"],
                         "Reconcile local PIDs and ETAs")

    def test_prepared_import_carries_credentials_but_no_secret(self):
        import subprocess
        import sys
        out = self.tmp / "n8n-import"
        (self.tmp / "conf" / "secrets.env").chmod(0o600)
        subprocess.run([sys.executable, "-I", str(WORKFLOW.parent / "prepare_workflow.py"), str(WORKFLOW), str(out),
                        str(self.tmp / "conf" / "secrets.env")], check=True, capture_output=True)
        wf = json.loads((out / "workflow.json").read_text())[0]
        self.assertIs(wf["active"], False)
        need = [n for n in wf["nodes"] if n["type"] in ("n8n-nodes-base.webhook", "n8n-nodes-base.httpRequest")]
        self.assertEqual(len(need), 9)
        self.assertTrue(all("httpHeaderAuth" in n["credentials"] for n in need))
        self.assertNotIn("b" * 32, (out / "workflow.json").read_text())
        self.assertEqual((out / "credentials.json").stat().st_mode & 0o777, 0o600)
        creds = {c["name"]: c["data"] for c in json.loads((out / "credentials.json").read_text())}
        self.assertEqual(sorted(d["name"] for d in creds.values()), ["X-TriAgent-Key", "X-TriAgent-Wake"])


class PlannerContextTests(BrokerCase):
    mode = "live"

    def test_planner_receives_the_full_market_id(self):
        cid = "0x" + "ab" * 32
        self.store.execute("INSERT INTO alerts(created,address,condition_id,trade_ts,usdc,score,flags_json,features_json) "
                           "VALUES (?,?,?,?,?,?,?,?)", (now(), "0x" + "a" * 40, cid, now(), 9000, 4, "[]", "{}"))
        seen = []
        with patch("triagent.providers.plan", side_effect=lambda cfg, store, ctx: seen.append(ctx) or {"tasks": []}):
            self.sup.tick_planner(force=True)
        self.assertIn(cid, seen[0])  # a 12-character prefix left a mission unable to find its market (07/11)


class MissionBriefTests(BrokerCase):
    def test_a_task_naming_an_alert_gets_its_exact_data(self):
        wallet, cid = "0x" + "b6" * 20, "0x" + "73" * 32
        self.store.execute("INSERT INTO alerts(created,address,condition_id,trade_ts,usdc,score,flags_json,features_json) "
                           "VALUES (?,?,?,?,?,?,?,?)", (now(), wallet, cid, 1794000000, 9769, 4, '["SHARED_FUNDER"]',
                                                        json.dumps({"features": {"n_trades_before": 7}, "funders": []})))
        jid = self.store.enqueue("claude", "analysis", "planned from an alert 2026",
                                 f"Test the four-flag alert around {wallet} and the same-market gap.", origin="planner")
        mdir, _ = providers.prepare_mission(self.cfg, self.store, self.store.job(jid))
        brief = (mdir / "MISSION.md").read_text()
        self.assertIn(cid, brief)  # 07/11: the planned mission stopped because the market id was not given
        self.assertIn('"n_trades_before":7', brief)
