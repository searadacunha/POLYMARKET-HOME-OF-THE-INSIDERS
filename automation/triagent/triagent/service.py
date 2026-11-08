"""Supervisor: queue, workers, reviews, planner, collector, recovery and the local web page."""
from __future__ import annotations

import hmac
import json
import logging
import os
import shutil
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from . import accounts, broker, inventory, polymarket, providers, schemas
from .config import CODE_DIR, Config
from .store import Store, canonical, now
from .util import ProviderError, redact, validate

LOG = logging.getLogger("triagent")
PROVIDER_OF = {"claude": "claude", "grok": "xai"}
OPENAI_LABEL = {"api": "api (OPENAI_API_KEY)",
                "codex_cli": "codex_cli: Codex CLI on the ChatGPT subscription (not the ChatGPT browser)",
                "chatgpt_gui": "chatgpt_gui: blocked, not implemented"}


class Supervisor:
    def __init__(self, cfg: Config, store: Store):
        self.cfg, self.store = cfg, store
        self.stop = threading.Event()
        self.procs: dict[str, Any] = {}
        self.n8n = cfg.get("ORCHESTRATOR") == "n8n"  # then only the broker starts provider work
        self.poll_lock = threading.Lock()  # the 10 s loop and n8n's reconcile must not collect a result twice

    # ------------------------------------------------------------ gates and holds
    def disk_free_gb(self) -> float:
        return shutil.disk_usage(self.cfg.state_dir).free / 1e9

    def gate(self) -> str:
        if self.cfg.kill_file.exists():
            return "kill switch present"
        if self.store.get_kv("paused") == "1":
            return "paused"
        if self.disk_free_gb() < self.cfg.float("DISK_MIN_FREE_GB"):
            return f"disk below {self.cfg.get('DISK_MIN_FREE_GB')} GB free"
        return ""

    def hold(self, provider: str, seconds: int, reason: str):
        self.store.set_kv(f"hold_{provider}", canonical({"until": now() + seconds, "reason": reason[:300]}))
        self.store.log("provider", f"{provider} on hold {seconds}s: {reason}", level="warning")
        self.store.emit("provider.blocked", job_id=provider)

    def held(self, provider: str) -> str:
        raw = self.store.get_kv(f"hold_{provider}")
        if not raw:
            return ""
        h = json.loads(raw)
        return h["reason"] if h["until"] > now() else ""

    def on_provider_error(self, provider: str, exc: ProviderError) -> int:
        """Returns the hold applied, in seconds."""
        if exc.kind == "budget":
            secs = 86400 - now() % 86400 + 60
        elif exc.kind == "auth":
            secs = 3600
        elif exc.kind == "transient":
            n = int(self.store.get_kv(f"backoff_{provider}", "0")) + 1
            self.store.set_kv(f"backoff_{provider}", n)
            secs = int(exc.retry_after or min(3600, 60 * 2 ** n))
        else:
            secs = 0
        if secs:
            self.hold(provider, secs, f"{exc.kind}: {exc}")
        return secs

    # ------------------------------------------------------------ recovery
    def recover(self):
        for provider in ("claude", "openai", "xai"):  # credentials may have been fixed before this restart
            if self.held(provider).startswith("auth"):
                self.store.execute("DELETE FROM kv WHERE key=?", (f"hold_{provider}",))
        for job in self.store.jobs("status='running'", limit=1000):
            if job["agent"] == "claude":
                mdir = Path(job["mission_dir"] or "")
                if providers.pid_alive(job["pid"], "claude"):
                    self.store.log("recovery", "adopted running Claude mission", job_id=job["id"])
                elif (mdir / "claude_output.json").is_file() and (mdir / "claude_output.json").stat().st_size:
                    self.store.log("recovery", "Claude mission finished while supervisor was down", job_id=job["id"])
                else:
                    self.store.set_status(job["id"], "blocked", "interrupted before a result was written; the "
                                          "provider may have run and billed it. Check, then `triagent retry`.")
            else:
                self.store.set_status(job["id"], "blocked", "interrupted during a synchronous Grok call; billing "
                                      "and result unknown. Check xAI usage, then `triagent retry`.")
        self.store.log("recovery", f"startup recovery done; counts {self.store.counts()}")

    # ------------------------------------------------------------ Claude worker
    def poll_claude(self):
        """Local only (process table and files, never a model): notice finished or overdue missions."""
        with self.poll_lock:
            self._poll_claude()

    def _poll_claude(self):
        for job in self.store.jobs("agent='claude' AND status='running'", limit=10):
            proc = self.procs.get(job["id"])
            alive = proc.poll() is None if proc else providers.pid_alive(job["pid"], "claude")
            if alive:
                if job["deadline"] and now() > job["deadline"]:  # the explicit budget, not an ETA
                    providers.kill_group(job["pid"])
                    self.store.set_status(job["id"], "failed", "timeout: mission killed at its deadline")
                    self.store.run_end(job["id"], "timeout", "claude_code")
                    self.release_lease(job["id"], "timeout")
                continue
            self.procs.pop(job["id"], None)
            self.finish_claude(job)
            self.release_lease(job["id"], "process ended")

    def release_lease(self, work_id: str, outcome: str):
        if self.store.execute("UPDATE leases SET state='finished', ended=?, outcome=? WHERE work_id=? AND "
                              "state='dispatched'", (now(), outcome[:200], work_id)):
            self.store.emit("work.ready", job_id=work_id)  # a worker slot is free again

    def tick_claude(self):
        self.poll_claude()
        if self.gate() or self.held("claude"):
            return
        if self.store.jobs("agent='claude' AND status='running'", limit=1):
            return  # one Claude mission at a time
        ok, why = providers.budget_ok(self.store, self.cfg, "claude", 0)
        if not ok:
            self.hold("claude", 86400 - now() % 86400 + 60, why)
            return
        job = self.store.claim("claude")
        if job:
            self.launch_claude(job)

    def launch_claude(self, job: dict):
        if job["attempts"] > 3:
            self.store.set_status(job["id"], "failed", "too many attempts")
            return
        try:
            proc = providers.claude_launch(self.cfg, self.store, job)
            if proc:
                self.procs[job["id"]] = proc
            self.store.run_start("claude_code", job["kind"], job["id"], mode=self.mode_label("claude"),
                                 model=self.cfg.get("CLAUDE_MODEL"), session_id=job.get("session_id"),
                                 queued_at=job["created"], attempts=job["attempts"])
            self.store.log("mission", f"Claude {job['kind']} started: {job['task'][:160]}", job_id=job["id"])
        except Exception as exc:  # launch failed before the provider ran: safe to requeue later
            self.store.set_status(job["id"], "queued", f"launch failed: {exc}"[:500])
            self.hold("claude", 600, f"launch failed: {exc}")
        if not self.cfg.live:
            self.finish_claude(self.store.job(job["id"]))

    def mode_label(self, agent: str) -> str:
        if not self.cfg.live:
            return "dryrun"
        return {"claude": self.cfg.get("CLAUDE_AUTH"), "gpt": self.cfg.get("OPENAI_MODE"),
                "grok": self.cfg.get("GROK_MODE")}[agent]

    def finish_claude(self, job: dict):
        state, payload = providers.claude_collect(self.cfg, job)
        self.store.run_end(job["id"], state, "claude_code")
        mdir = Path(job["mission_dir"])
        providers.register_evidence(self.store, mdir, job["id"])
        if state == "ok":
            report, usd, meta = payload
            self.store.add_cost("claude", usd, job_id=job["id"],
                                estimated=self.cfg.get("CLAUDE_AUTH") != "api", units=meta)
            if job["kind"] == "develop":
                report["code_changes"] = (report.get("code_changes") or "") + "\n" + providers.dev_commit(self.cfg, job)
            self.store.save_result(job["id"], {"report": report, "meta": meta})
            self.store.log("mission", f"Claude result stored ({meta.get('num_turns')} turns, ${usd:.2f})", job_id=job["id"])
            return
        err = (mdir / "claude_stderr.log").read_text(errors="replace")[-600:] if (mdir / "claude_stderr.log").is_file() else ""
        text = f"{payload} {err}".lower()
        if any(s in text for s in ("not logged in", "invalid api key", "authentication", "oauth", "/login")):
            self.store.set_status(job["id"], "queued", "claude authentication failed; mission requeued")
            self.hold("claude", 3600, "authentication: " + redact(err[-200:] or str(payload)))
        elif state == "lost":
            self.store.set_status(job["id"], "blocked", str(payload))
        else:
            self.store.set_status(job["id"], "failed", redact(str(payload) + " " + err[-300:]))

    # ------------------------------------------------------------ Grok worker
    def expire_grok(self):
        with self.poll_lock:
            self._expire_grok()

    def _expire_grok(self):
        for job in self.store.jobs("agent='grok' AND status='awaiting_external_result'", limit=50):
            if job["deadline"] and now() > job["deadline"]:
                self.store.set_status(job["id"], "failed", "no Grok Bot result before the deadline "
                                      "(a webhook acknowledgement is not a completed task)")

    def tick_grok(self):
        self.expire_grok()
        if self.gate() or self.held("xai"):
            return
        job = self.store.claim("grok")
        if job:
            self.run_grok(job)

    def run_grok(self, job: dict):
        self.store.run_start(self.cfg.get("GROK_MODE"), "x_research", job["id"], mode=self.mode_label("grok"),
                             queued_at=job["created"], attempts=job["attempts"])
        try:
            if self.cfg.get("GROK_MODE") == "bot":
                providers.grok_bot_trigger(self.cfg, self.store, job)
                self.store.log("mission", "Grok Bot routine triggered; awaiting authenticated callback", job_id=job["id"])
                return
            _, (report, usd, meta) = providers.grok_run(self.cfg, self.store, job)
            self.store.run_end(job["id"], "ok")
            self.store.save_result(job["id"], {"report": report, "meta": meta})
            self.store.log("mission", f"Grok result stored (${usd:.2f})", job_id=job["id"])
        except ProviderError as exc:
            self.store.run_end(job["id"], exc.kind)
            if exc.kind in ("budget", "auth", "transient"):
                self.store.set_status(job["id"], "queued", f"waiting: {exc}")
                self.on_provider_error("xai", exc)
            elif exc.kind == "uncertain":
                self.store.set_status(job["id"], "blocked", f"uncertain: {exc}. Check xAI usage, then retry.")
            else:
                self.store.set_status(job["id"], "failed", str(exc))

    # ------------------------------------------------------------ OpenAI reviewer
    def tick_review(self):
        if self.gate() or self.held("openai"):
            return
        for job in self.store.jobs("status='reviewing'", limit=3):
            if self.review_one(job):
                return

    def review_one(self, job: dict) -> int:
        """One audit in a fresh session; returns the provider hold applied (seconds), 0 when none."""
        gpt = "codex_cli" if self.cfg.get("OPENAI_MODE") == "codex_cli" else "openai_api"
        self.store.run_start(gpt, "review", job["id"], mode=self.mode_label("gpt"), queued_at=job["updated"],
                             model=self.cfg.get("CODEX_MODEL") if gpt == "codex_cli" else self.cfg.get("OPENAI_MODEL"),
                             attempts=job["review_attempts"] + 1)
        try:
            self.review(job)
            self.store.run_end(job["id"], "ok", gpt)
            return 0
        except ProviderError as exc:
            self.store.run_end(job["id"], exc.kind, gpt)
            secs = self.on_provider_error("openai", exc)
            if exc.kind in ("uncertain", "permanent"):
                attempts = job["review_attempts"] + 1
                self.store.execute("UPDATE jobs SET review_attempts=? WHERE id=?", (attempts, job["id"]))
                if attempts >= 3:
                    self.store.set_status(job["id"], "blocked", f"review failed 3 times: {exc}")
            else:
                self.store.set_status(job["id"], "reviewing", f"waiting: {exc}")
            return secs

    def review(self, job: dict):
        stored = json.loads(job["result_json"])
        report = stored["report"]
        checks: dict[str, Any] = {"result_sha256": job["result_sha256"],
                                  "collector_alerts": providers.named_alerts(self.store, job["task"])}
        if job["agent"] == "claude":
            mdir = Path(job["mission_dir"])
            checks["evidence"] = providers.evidence_check(self.cfg, mdir, report)
            if self.cfg.live:
                checks["edges"] = polymarket.verify_reported_edges(self.cfg, self.store, job["id"],
                                                                   report.get("edges", []))
        else:
            checks["citations_returned"] = len(stored.get("meta", {}).get("citations", []))
            if self.cfg.live:  # an X post cited by Grok counts only once the supervisor has re-read it
                checks["x_posts"] = providers.verify_x_leads(report.get("leads", []))
        verdict = providers.review(self.cfg, self.store, job, report, checks, inventory.digest(self.store))
        self.apply_review(job, report, verdict, checks)

    def apply_review(self, job: dict, report: dict, verdict: dict, checks: dict) -> int:
        inv, cfg = job["investigation"], self.cfg
        for claim in verdict.get("claims", []):
            self.store.add_finding(inv, job["id"], "claim", claim["statement"], tier=claim["tier"],
                                   evidence=claim.get("evidence_ids"))
        for q in report.get("unresolved", []):
            self.store.add_finding(inv, job["id"], "question", q)
        for n in report.get("negative_results", []):
            self.store.add_finding(inv, job["id"], "negative", n, tier="REFUTED")
        for m in report.get("methods_used", []):
            self.store.add_finding(inv, job["id"], "method", f"{m['method']} [{m['scope']}] -> {m['outcome']}",
                                   window=(m["window_start"], m["window_end"]), version=m["version"])
        for t in verdict.get("falsification_tests", [])[:5]:
            self.store.add_finding(inv, job["id"], "test", t)
        for w in report.get("wallets_examined", [])[:200]:
            if isinstance(w, str) and w.startswith("0x") and len(w) == 42:
                self.store.execute("INSERT INTO wallets(address,first_seen,examined_by) VALUES (?,?,?) "
                                   "ON CONFLICT(address) DO UPDATE SET examined_by=excluded.examined_by",
                                   (w.lower(), now(), job["id"]))
        novelty = int(verdict.get("novelty", 0))
        found = self.store.investigation(inv) or {}
        streak = found.get("low_novelty_streak", 0) + 1 if novelty <= 1 else 0
        stop = verdict["decision"] != "continue" or streak >= cfg.int("STOP_AFTER_LOW_NOVELTY")
        self.store.execute("UPDATE investigations SET low_novelty_streak=?, updated=?, status=? WHERE id=?",
                           (streak, now(), "exhausted" if stop else "open", inv))
        added = 0
        if not stop and novelty >= cfg.int("MIN_NOVELTY_FOLLOWUP"):
            for f in verdict.get("followups", [])[:cfg.int("MAX_CHILDREN")]:
                kind = "x_research" if f["agent"] == "grok" else ("develop" if f["kind"] == "develop" else "analysis")
                try:
                    if self.store.enqueue(f["agent"], kind, f["novelty_key"], f["task"], origin="review",
                                          investigation=inv, parent=job["id"], depth=job["depth"] + 1,
                                          falsifier=f["falsifier"], priority=f["expected_information_gain"],
                                          max_depth=cfg.int("MAX_DEPTH")):
                        added += 1
                except ValueError as exc:
                    self.store.log("review", f"follow-up discarded: {exc}", level="warning", job_id=job["id"])
        self.store.set_status(job["id"], "done", f"reviewed: novelty {novelty}, {verdict['decision']}, "
                              f"{added} follow-up(s)" + ("; investigation stopped" if stop else ""),
                              review_json=canonical({**verdict, "checks": checks, "enqueued": added}),
                              novelty=novelty, decision=verdict["decision"])
        # second phase of an alert: its mission has been cross-checked (which says nothing of guilt)
        self.store.execute("UPDATE alerts SET status='reviewed' WHERE job_id=?", (job["id"],))
        self.store.log("review", f"novelty {novelty}, {verdict['decision']}, {added} follow-up(s)", job_id=job["id"])
        return added

    # ------------------------------------------------------------ planner and maintenance
    def tick_planner(self, force: bool = False):
        last = int(self.store.get_kv("last_plan", "0"))
        if not force and (now() - last < self.cfg.int("DISCOVERY_SECONDS") or self.gate() or self.held("openai")):
            return
        if not self.cfg.live:
            return
        self.store.set_kv("last_plan", now())  # set first: an error must not cause a paid retry loop
        questions = [f"- {f['text']}" for f in self.store.query(
            "SELECT text FROM findings WHERE type='question' ORDER BY id DESC LIMIT 40")]
        alerts = [f"- {a['address']} {a['usdc']:.0f} USDC cid {a['condition_id']} flags {a['flags_json']} "
                  f"status {a['status']}" for a in self.store.query(
                      "SELECT * FROM alerts ORDER BY score DESC, created DESC LIMIT 20")]
        closed = [f"- {i['id']}: {i['title'][:100]}" for i in self.store.query(
            "SELECT id,title FROM investigations WHERE status!='open' LIMIT 60")]
        context = (f"INVENTORY:\n{inventory.digest(self.store)}\n\nOPEN QUESTIONS:\n{chr(10).join(questions)}\n\n"
                   f"AUTOMATIC ALERTS (selection signals only):\n{chr(10).join(alerts)}\n\n"
                   f"STOPPED INVESTIGATIONS:\n{chr(10).join(closed)}\n\n"
                   f"EXISTING NOVELTY KEYS: {canonical(self.store.recent_keys(150))}")
        work = f"plan-{now()}"
        self.store.run_start("codex_cli" if self.cfg.get("OPENAI_MODE") == "codex_cli" else "openai_api", "plan",
                             work, mode=self.mode_label("gpt"))
        try:
            result = providers.plan(self.cfg, self.store, context)
            self.store.run_end(work, "ok")
        except ProviderError as exc:
            self.store.run_end(work, exc.kind)
            self.on_provider_error("openai", exc)
            if exc.kind in ("auth", "budget", "transient"):  # nothing was billed: plan again once the hold ends
                self.store.set_kv("last_plan", last)
            return
        added = 0
        for t in result.get("tasks", [])[:3]:
            kind = "x_research" if t["agent"] == "grok" else ("develop" if t["kind"] == "develop" else "analysis")
            try:
                added += bool(self.store.enqueue(t["agent"], kind, t["novelty_key"], t["task"], origin="planner",
                                                 falsifier=t["falsifier"], priority=t["expected_information_gain"]))
            except ValueError as exc:
                self.store.log("planner", f"task discarded: {exc}", level="warning")
        self.store.log("planner", f"{added} new mission(s)" + ("" if added else f": {result.get('no_useful_lead_reason', '')}")
                       + (f" [request {result['_provider']['request_id']}]" if result.get("_provider") else ""))

    def tick_maintenance(self):
        if now() - int(self.store.get_kv("last_backup", "0")) > 86400:
            self.store.backup(self.cfg.state_dir / "backups")
            self.store.set_kv("last_backup", now())
        if now() - int(self.store.get_kv("inventory_built", "0")) > 86400 and self.cfg.repo_dir.exists():
            try:
                if self.cfg.live:
                    self.store.set_kv("research_repo_head", inventory.refresh_repo(self.cfg))
                inventory.build(self.cfg, self.store)
            except Exception as exc:
                self.store.log("inventory", f"inventory refresh failed: {exc}", level="warning")
                self.store.set_kv("inventory_built", now())

    # ------------------------------------------------------------ loops
    def agents_loop(self):
        # With n8n, the historical scheduler is off: this loop only watches local processes and maintains.
        steps = ((self.poll_claude, self.expire_grok, self.tick_maintenance) if self.n8n else
                 (self.tick_claude, self.tick_grok, self.tick_review, self.tick_planner, self.tick_maintenance))
        while not self.stop.is_set():
            for step in steps:
                try:
                    step()
                except Exception as exc:
                    LOG.exception("%s failed", step.__name__)
                    self.store.log("supervisor", f"{step.__name__}: {exc}", level="error")
            self.stop.wait(10)

    def collector_loop(self):
        while not self.stop.is_set():
            wait = self.cfg.int("COLLECT_SECONDS")
            if self.cfg.live and not self.gate():
                try:
                    self.store.set_kv("feed_status", canonical(polymarket.feed_status()))
                    summary = polymarket.collect_trades(self.cfg, self.store)
                    summary.update(polymarket.scan(self.cfg, self.store))
                    self.store.set_kv("collector_last", canonical(summary))
                    self.store.set_kv("backoff_polymarket", 0)
                    if not summary.get("reached_checkpoint", True):  # backlog: catch up faster
                        wait = self.cfg.int("COLLECT_FAST_SECONDS")
                except ProviderError as exc:
                    self.store.log("collector", f"{exc.kind}: {exc}", level="warning")
                    self.stop.wait(min(900, 60 * 2 ** int(self.store.get_kv("backoff_polymarket", "0"))))
                    self.store.set_kv("backoff_polymarket", int(self.store.get_kv("backoff_polymarket", "0")) + 1)
                except Exception as exc:
                    LOG.exception("collector")
                    self.store.log("collector", str(exc), level="error")
            self.stop.wait(wait)

    def accounts_loop(self):
        """Shadow record of new accounts: recorded only, no alert, no mission, no notification."""
        failures = 0
        while not self.stop.is_set():
            if self.cfg.live and self.cfg.get("ACCOUNTS_SHADOW") == "1" and not self.gate():
                try:
                    self.store.set_kv("accounts_last", canonical({**accounts.tick(self.cfg, self.store), "at": now()}))
                    failures = 0
                except ProviderError as exc:
                    failures += 1
                    self.store.log("accounts", f"{exc.kind}: {exc}", level="warning")
                    self.stop.wait(min(900, 60 * 2 ** failures))
                except Exception as exc:
                    LOG.exception("accounts")
                    self.store.log("accounts", str(exc), level="error")
            self.stop.wait(60)

    def watchdog(self):
        while not self.stop.is_set():
            if self.cfg.kill_file.exists():
                self.kill_all("kill switch file present")
                self.stop.set()
            self.stop.wait(2)

    def kill_all(self, reason: str):
        for job in self.store.jobs("status='running'", limit=100):
            if job["agent"] == "claude":
                providers.kill_group(job["pid"])
            self.store.set_status(job["id"], "blocked", f"stopped by {reason}")


# ---------------------------------------------------------------- web page + callback
def state_snapshot(sup: Supervisor) -> dict:
    s, cfg = sup.store, sup.cfg
    day = now() - now() % 86400
    spend = {p: dict(zip(("usd_today", "calls_today"), s.spent(p, day))) for p in ("claude", "openai", "xai")}
    agents = {
        "claude": {"mode": cfg.get("CLAUDE_AUTH"), "model": cfg.get("CLAUDE_MODEL"), "hold": sup.held("claude")},
        "openai": {"mode": OPENAI_LABEL.get(cfg.get("OPENAI_MODE"), cfg.get("OPENAI_MODE")),
                   "model": (cfg.get("CODEX_MODEL") or "Codex default") if cfg.get("OPENAI_MODE") == "codex_cli"
                   else cfg.get("OPENAI_MODEL"),
                   "configured": {"api": bool(cfg.secret("OPENAI_API_KEY")),
                                  "codex_cli": Path(cfg.get("CODEX_BIN")).exists()}.get(cfg.get("OPENAI_MODE"), False),
                   "hold": sup.held("openai")},
        "grok": {"mode": cfg.get("GROK_MODE"), "configured": bool(cfg.secret("XAI_API_KEY")) or cfg.get("GROK_MODE") == "grok_cli",
                 "hold": sup.held("xai")},
    }
    for name, provider in (("claude", "claude"), ("openai", "openai"), ("grok", "xai")):
        agents[name].update(spend[provider])
    cols = ("id,agent,kind,status,status_reason,substr(task,1,400) AS task,novelty,decision,investigation,origin,"
            "cost_usd,updated,parent,depth,substr(json_extract(result_json,'$.report.summary'),1,700) AS summary")
    return {
        "now": now(), "mode": cfg.get("RUN_MODE"), "gate": sup.gate() or "running",
        "orchestrator": cfg.get("ORCHESTRATOR"), "durations": broker.estimates(s, cfg),
        "feed": json.loads(s.get_kv("feed_status") or "{}"),
        "new_accounts": {**s.query("SELECT count(*) n, sum(first_deposit_tx IS NOT NULL) funded, sum(funder IS NOT NULL) "
                                   "traced, min(observed_at) since FROM new_accounts")[0],
                         "last": json.loads(s.get_kv("accounts_last") or "{}")},
        "funding_bursts": accounts.bursts(s),
        "leases": s.query("SELECT work_id,agent,task_type,state,created,ended,outcome FROM leases ORDER BY created "
                          "DESC LIMIT 15"),
        "disk_free_gb": round(sup.disk_free_gb(), 2), "counts": s.counts(), "agents": agents,
        "collector": {"last_ok": s.get_kv("last_collect_ok"), "checkpoint": s.get_kv("trades_checkpoint_ts"),
                      "last": json.loads(s.get_kv("collector_last") or "{}"),
                      "trades": s.query("SELECT count(*) n FROM trades")[0]["n"],
                      "wallets_profiled": s.query("SELECT count(*) n FROM wallets WHERE profiled_at IS NOT NULL")[0]["n"]},
        "active": s.query(f"SELECT {cols} FROM jobs WHERE status IN ('queued','running','awaiting_external_result','reviewing') ORDER BY priority DESC, created LIMIT 50"),
        "recent": s.query(f"SELECT {cols} FROM jobs WHERE status IN ('done','failed','blocked','paused') ORDER BY updated DESC LIMIT 40"),
        "alerts": s.query("SELECT id,created,address,condition_id,trade_ts,usdc,score,level,notified_at,flags_json,status,job_id FROM alerts ORDER BY score DESC, created DESC LIMIT 60"),
        "wallets": s.query("SELECT address,profiled_at,first_activity_ts,first_deposit_ts,first_trade_ts,n_events,truncated FROM wallets WHERE profiled_at IS NOT NULL ORDER BY profiled_at DESC LIMIT 40"),
        "edges": s.query("SELECT src,dst,kind,chain,tx_hash,token,amount,ts,method,level,evidence_sha256,job_id FROM edges ORDER BY id DESC LIMIT 80"),
        "findings": s.query("SELECT investigation,job_id,type,text,tier,evidence_json,created FROM findings WHERE type IN ('claim','negative','question') ORDER BY id DESC LIMIT 60"),
        "investigations": s.query("SELECT id,title,status,low_novelty_streak,updated FROM investigations ORDER BY updated DESC LIMIT 40"),
        "events": s.query("SELECT ts,level,kind,job_id,message FROM events ORDER BY id DESC LIMIT 60"),
        "costs_total": s.query("SELECT provider, round(sum(usd),4) usd, count(*) calls FROM costs GROUP BY provider"),
    }


GROK_CALLBACK = schemas.GROK_REPORT | {"properties": {**schemas.GROK_REPORT["properties"],
                                                      "job_id": {"type": "string"}, "nonce": {"type": "string"}},
                                       "required": ["job_id", "nonce", "summary"]}


def make_handler(sup: Supervisor):
    port = sup.cfg.int("HTTP_PORT")
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, code: int, body: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("content-type", ctype)
            self.send_header("cache-control", "no-store")
            self.send_header("x-content-type-options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def host_ok(self) -> bool:  # refuses DNS-rebinding pages that would read the dashboard
            return self.headers.get("Host", "") in allowed_hosts

        def do_GET(self):
            if not self.host_ok():
                return self.send(403, b'{"error":"host"}')
            if self.path == "/":
                return self.send(200, (CODE_DIR / "triagent" / "ui.html").read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/state":
                return self.send(200, json.dumps(state_snapshot(sup), default=str).encode())
            if self.path == "/health":
                return self.send(200, json.dumps({"ok": True, "gate": sup.gate() or "running"}).encode())
            self.send(404, b'{"error":"not found"}')

        def do_POST(self):
            if self.path != "/api/grok-complete":
                return self.send(404, b'{"error":"not found"}')
            code, body = grok_callback(sup, self.headers.get("Authorization"), self.rfile,
                                       int(self.headers.get("Content-Length") or 0))
            self.send(code, json.dumps(body).encode())

    return Handler


def grok_callback(sup: Supervisor, authorization: str | None, stream, length: int) -> tuple[int, dict]:
    """Authenticated Grok Bot completion: stored durably before the 200 is returned."""
    secret = sup.cfg.secret("GROK_CALLBACK_SECRET")
    if not secret or not authorization or not hmac.compare_digest(authorization.encode(), f"Bearer {secret}".encode()):
        return 401, {"error": "unauthorized"}
    if not 0 < length <= 1_000_000:
        return 413, {"error": "size"}
    try:
        payload = json.loads(stream.read(length))
    except json.JSONDecodeError:
        return 400, {"error": "json"}
    errors = validate(payload, GROK_CALLBACK) if isinstance(payload, dict) else ["not an object"]
    if errors:
        return 400, {"error": "schema", "details": errors[:5]}
    job = sup.store.job(str(payload["job_id"]))
    if not job or job["agent"] != "grok" or job["status"] != "awaiting_external_result":
        return 409, {"error": "not awaiting this callback"}
    if not hmac.compare_digest(str(job["external_nonce"] or "").encode(), str(payload["nonce"]).encode()):
        return 403, {"error": "nonce"}
    report = {k: payload.get(k, [] if k != "summary" else "") for k in schemas.GROK_REPORT["properties"]}
    sup.store.save_result(job["id"], {"report": report, "meta": {"mode": "bot", "callback_at": now()}})
    sup.store.log("mission", "Grok Bot result received and authenticated", job_id=job["id"])
    return 200, {"accepted": True, "stored": True}


def run(cfg: Config):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if cfg.kill_file.exists():
        LOG.warning("kill switch %s present: not starting (remove it with `triagent start`)", cfg.kill_file)
        return 0
    store = Store(cfg.db_path)
    if not store.integrity_ok():
        LOG.error("database integrity check failed; refusing to run. Restore from %s", cfg.state_dir / "backups")
        return 2
    sup = Supervisor(cfg, store)
    sup.recover()
    bro = broker.Broker(sup)
    bro.recover()
    server = ThreadingHTTPServer(("127.0.0.1", cfg.int("HTTP_PORT")), make_handler(sup))
    loops = [sup.agents_loop, sup.collector_loop, sup.accounts_loop, sup.watchdog, server.serve_forever, bro.bus_loop]
    if cfg.secret("BROKER_TOKEN"):  # loopback only, and refuses every request without the token
        loops.append(ThreadingHTTPServer(("127.0.0.1", cfg.int("BROKER_PORT")), broker.make_handler(bro)).serve_forever)
    else:
        LOG.warning("BROKER_TOKEN missing: the n8n broker is not started")
    threads = [threading.Thread(target=f, name=getattr(f, "__name__", "loop"), daemon=True) for f in loops]
    for t in threads:
        t.start()
    store.log("supervisor", f"started in {cfg.get('RUN_MODE')} mode, pid {os.getpid()}")

    def shutdown(*_):
        sup.stop.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    while not sup.stop.is_set():
        sup.stop.wait(1)
    server.shutdown()
    store.log("supervisor", "stopped cleanly; running missions keep running and are adopted at next start")
    return 0
