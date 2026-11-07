"""Local broker between n8n and the supervisor (127.0.0.1 only, header-authenticated).

n8n decides WHEN to look for work (an event, or its 15-minute recovery timer); the broker decides WHAT may run,
under one lock and SQLite constraints: single-use leases, one session per provider at a time, holds, budgets,
disk gate. Dispatch only starts the process and answers 202; completion comes back as an event. Reconcile reads
the process table and files and never calls a model. Contract: n8n/TRIAGENT_N8N_ADAPTIVE_V2.json.
"""
from __future__ import annotations

import hmac
import json
import logging
import math
import re
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

from . import detector, providers
from .store import EVENT_TYPES, canonical, now
from .util import ProviderError, http

LOG = logging.getLogger("triagent.broker")
EVENT_ID = re.compile(r"^[A-Za-z0-9_.:-]{8,120}$")
AGENT_PROVIDER = {"gpt": "openai", "claude": "claude", "grok": "xai"}
MIN_SAMPLES = 5


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def estimates(store, cfg) -> list[dict]:
    """Observed durations per provider and task type. Below MIN_SAMPLES no ETA is claimed: the bound is the
    configured hard timeout. The ETA feeds the page and stall labels only; it never resends a prompt."""
    groups: dict[tuple, list[float]] = {}
    for r in store.query("SELECT provider, task_type, runtime_sec FROM runs WHERE runtime_sec IS NOT NULL "
                         "AND exit_status='ok' AND mode!='dryrun'"):
        groups.setdefault((r["provider"], r["task_type"]), []).append(float(r["runtime_sec"]))
    bound = {"claude_code": "CLAUDE_TIMEOUT_S", "codex_cli": "CODEX_TIMEOUT_S", "openai_api": "CODEX_TIMEOUT_S"}
    out = []
    for (provider, task), vals in sorted(groups.items()):
        n = len(vals)
        row = {"provider": provider, "task_type": task, "n": n, "min_s": round(min(vals)), "max_s": round(max(vals)),
               "hard_timeout_s": cfg.int(bound.get(provider, "GROK_TIMEOUT_S"))}
        if n >= MIN_SAMPLES:
            row.update(p50_s=round(percentile(vals, .5)), p90_s=round(percentile(vals, .9)),
                       p99_s=round(percentile(vals, .99)) if n >= 30 else None,
                       confidence="low (n<20)" if n < 20 else "empirical")
        else:
            row.update(p50_s=None, p90_s=None, p99_s=None, confidence=f"insufficient data (n={n}<{MIN_SAMPLES})")
        out.append(row)
    return out


def macos_notify(title: str, message: str) -> bool:
    script = "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run"
    try:  # text travels as arguments, never inside the AppleScript source
        return subprocess.run(["osascript", "-e", script, title[:120], message[:400]], capture_output=True,
                              timeout=15).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


class Broker:
    def __init__(self, sup):
        self.sup, self.store, self.cfg = sup, sup.store, sup.cfg
        self.lock = threading.Lock()
        self.inflight: dict[str, threading.Thread] = {}
        self.notifier = macos_notify

    # ------------------------------------------------------------ events
    def ingest(self, body: dict) -> tuple[int, dict]:
        event_id, event_type = str(body.get("event_id", "")), str(body.get("event_type", ""))
        if event_type not in EVENT_TYPES or not EVENT_ID.match(event_id):
            return 400, {"error": "invalid event_type or event_id"}
        alert_id = str(body.get("alert_id") or "")[:100]
        with self.lock:
            row = self.store.query("SELECT ingested_at, alert_id FROM bus WHERE event_id=?", (event_id,))
            if row and row[0]["ingested_at"]:
                return 200, {"event_id": event_id, "event_type": event_type, "duplicate": True,
                             "alert_id": row[0]["alert_id"], "alert_ready": False}
            if row:
                self.store.execute("UPDATE bus SET ingested_at=? WHERE event_id=?", (now(), event_id))
                alert_id = row[0]["alert_id"] or alert_id
            else:  # an event that did not come from this broker (manual test, another tool)
                self.store.execute("INSERT INTO bus(event_id,event_type,job_id,alert_id,created,origin,sent_at,"
                                   "ingested_at) VALUES (?,?,?,?,?,?,0,?)",
                                   (event_id, event_type, str(body.get("job_id") or "")[:100], alert_id, now(),
                                    "external", now()))
        ready = event_type == "alert.early" and alert_id.isdigit() and not self.notify_refusal(int(alert_id))
        return 200, {"event_id": event_id, "event_type": event_type, "duplicate": False, "alert_id": alert_id,
                     "alert_ready": ready}

    # ------------------------------------------------------------ leases
    def availability(self) -> tuple[dict[str, str], dict[str, int]]:
        """Why each agent cannot start now ('' = it can), and the active leases per agent."""
        cfg, s, sup = self.cfg, self.store, self.sup
        active: dict[str, int] = {}
        for r in s.query("SELECT agent, count(*) n FROM leases WHERE state IN ('open','dispatched') GROUP BY agent"):
            active[r["agent"]] = r["n"]
        why = {}
        for agent, provider in AGENT_PROVIDER.items():
            reason = sup.held(provider) and f"{provider} on hold: {sup.held(provider)}"
            if not reason and active.get(agent):
                reason = f"a {agent} session is already running"
            if not reason and agent != "grok":
                ok, msg = providers.budget_ok(s, cfg, provider)
                reason = "" if ok else msg
            if not reason:
                reason = providers.unavailable(cfg, agent)
            why[agent] = reason or ""
        if s.jobs("agent='claude' AND status='running'", limit=1):
            why["claude"] = why["claude"] or "a Claude mission is running"
        if s.jobs("agent='grok' AND status IN ('running','awaiting_external_result')", limit=1):
            why["grok"] = why["grok"] or "a Grok task is running"
        return why, active

    def pick(self) -> tuple[tuple[str, str, str] | None, dict]:
        """(agent, task_type, work_id) of the most useful startable work, or None with the reasons."""
        if not self.sup.n8n:  # two schedulers would duplicate missions and spending
            return None, {"orchestrator": "ORCHESTRATOR=internal: the supervisor schedules, n8n may not start work"}
        gate = self.sup.gate()
        if gate:
            return None, {"gate": gate}
        why, _ = self.availability()
        leased = "SELECT work_id FROM leases WHERE state IN ('open','dispatched')"
        if not why["gpt"]:  # a stored result waits for its audit: first
            row = self.store.query(f"SELECT id FROM jobs WHERE status='reviewing' AND id NOT IN ({leased}) "
                                   "ORDER BY priority DESC, updated LIMIT 1")
            if row:
                return ("gpt", "review", row[0]["id"]), why
        for agent in ("claude", "grok"):
            if not why[agent]:
                row = self.store.query(f"SELECT id FROM jobs WHERE agent=? AND status='queued' AND id NOT IN "
                                       f"({leased}) ORDER BY priority DESC, created, id LIMIT 1", (agent,))
                if row:
                    return (agent, "x_research" if agent == "grok" else "mission", row[0]["id"]), why
        period = self.cfg.int("DISCOVERY_SECONDS")
        if not why["gpt"] and self.cfg.live and now() - int(self.store.get_kv("last_plan", "0")) >= period:
            return ("gpt", "plan", f"plan-{now() // period}"), why  # the budgeted periodic plan, nothing else
        return None, {k: v or "no queued work" for k, v in why.items()}

    def lease(self, _body: dict) -> tuple[int, dict]:
        with self.lock:
            self.store.execute("UPDATE leases SET state='expired', ended=? WHERE state='open' AND expires<?",
                               (now(), now()))
            choice, reasons = self.pick()
            if not choice:
                return 200, {"ready": False, "reasons": reasons}
            agent, task_type, work_id = choice
            lease_id = secrets.token_urlsafe(18)
            self.store.execute("INSERT INTO leases(lease_id,work_id,agent,task_type,created,expires,state) "
                               "VALUES (?,?,?,?,?,?,'open')",
                               (lease_id, work_id, agent, task_type, now(), now() + self.cfg.int("LEASE_TTL_S")))
        return 200, {"ready": True, "job_id": work_id, "lease_id": lease_id, "agent": agent, "task_type": task_type}

    def take(self, body: dict, state: str) -> tuple[dict | None, str]:
        """Consume an open lease exactly once (under the lock)."""
        lease_id, job_id = str(body.get("lease_id", "")), str(body.get("job_id", ""))
        rows = self.store.query("SELECT * FROM leases WHERE lease_id=?", (lease_id,))
        if not rows:
            return None, "unknown lease"
        lease = rows[0]
        if lease["state"] != "open":
            return None, f"lease already {lease['state']}"
        if lease["expires"] < now():
            self.store.execute("UPDATE leases SET state='expired', ended=? WHERE lease_id=?", (now(), lease_id))
            return None, "lease expired"
        if lease["work_id"] != job_id or ("agent" in body and body["agent"] != lease["agent"]):
            self.store.execute("UPDATE leases SET state='rejected', ended=?, outcome='mismatch' WHERE lease_id=?",
                               (now(), lease_id))
            return None, "lease does not match job or agent"
        self.store.execute("UPDATE leases SET state=? WHERE lease_id=? AND state='open'", (state, lease_id))
        return lease, ""

    def dispatch(self, body: dict) -> tuple[int, dict]:
        if body.get("fresh_session") is False:
            return 400, {"error": "only fresh sessions are supported"}
        with self.lock:
            gate = self.sup.gate()
            lease, err = self.take(body, "dispatched") if not gate else (None, f"gate: {gate}")
            if not lease:
                return 409, {"accepted": False, "error": err}
            agent, work_id, lease_id = lease["agent"], lease["work_id"], lease["lease_id"]
            if agent in ("claude", "grok"):
                job = self.store.claim(agent, work_id)
                if not job:
                    self.end_lease(lease_id, "rejected", "job no longer queued")
                    return 409, {"accepted": False, "error": "job no longer queued"}
            if agent == "claude":
                self.sup.launch_claude(job)  # its own process group; finish is noticed by poll_claude
                if self.store.job(work_id)["status"] != "running":
                    self.sup.release_lease(work_id, "launch failed or finished at once")
            else:
                target = {"grok": lambda: self.sup.run_grok(job),
                          "gpt": (lambda: self.sup.tick_planner(force=True)) if lease["task_type"] == "plan"
                          else (lambda: self.sup.review_one(self.store.job(work_id)))}[agent]
                thread = threading.Thread(target=self.run_async, args=(lease_id, work_id, target),
                                          name=f"{agent}-{work_id}", daemon=True)
                self.inflight[lease_id] = thread
                thread.start()
        if self.pick()[0]:
            self.store.emit("work.ready", job_id=work_id)  # more startable work: wake n8n again
        return 202, {"accepted": True, "async": True, "job_id": work_id, "agent": agent, "lease_id": lease_id}

    def run_async(self, lease_id: str, work_id: str, target):
        outcome = "ok"
        try:
            target()
        except Exception as exc:  # the provider code already stores its own errors; this is a bug guard
            outcome = f"error: {exc}"[:200]
            LOG.exception("async %s", work_id)
            self.store.log("broker", f"async run {work_id} crashed: {exc}", level="error", job_id=work_id)
        finally:
            self.inflight.pop(lease_id, None)
            self.end_lease(lease_id, "finished", outcome)
            self.store.emit("work.ready", job_id=work_id)

    def end_lease(self, lease_id: str, state: str, outcome: str):
        self.store.execute("UPDATE leases SET state=?, ended=?, outcome=? WHERE lease_id=?",
                           (state, now(), outcome[:200], lease_id))

    def reject(self, body: dict) -> tuple[int, dict]:
        with self.lock:
            lease, err = self.take(body, "rejected")
            if not lease:
                return 409, {"error": err}
            reason = str(body.get("reason", "rejected"))[:200]
            self.end_lease(lease["lease_id"], "rejected", reason)
            self.store.set_status(lease["work_id"], "blocked", f"rejected by n8n: {reason}",
                                  expect=("queued", "reviewing"))
        return 200, {"rejected": True, "job_id": lease["work_id"]}

    # ------------------------------------------------------------ reconcile (local only)
    def backfill_runs(self):
        """Once: durations already measured before this table existed (Claude JSON result, Codex files)."""
        if self.store.get_kv("runs_backfilled"):
            return
        for job in self.store.query("SELECT id, kind, created, started, result_json FROM jobs WHERE agent='claude' "
                                    "AND result_json IS NOT NULL"):
            ms = json.loads(job["result_json"]).get("meta", {}).get("duration_ms")
            if ms and self.cfg.live:
                self.store.execute("INSERT INTO runs(provider,task_type,work_id,mode,queued_at,started_at,finished_at,"
                                   "runtime_sec,exit_status,source) VALUES ('claude_code',?,?,?,?,?,?,?,'ok','backfill')",
                                   (job["kind"], job["id"], self.cfg.get("CLAUDE_AUTH"), job["created"],
                                    job["started"] or 0, (job["started"] or 0) + ms // 1000, ms / 1000))
        for answer in [*self.cfg.missions_dir.glob("*/reviews/*/answer.json"),
                       *(self.cfg.state_dir / "plans" / "reviews").glob("*/answer.json")]:
            prompt = answer.parent / "prompt.txt"
            if prompt.is_file() and self.cfg.live:
                t0, t1 = prompt.stat().st_mtime, answer.stat().st_mtime
                self.store.execute("INSERT INTO runs(provider,task_type,work_id,mode,started_at,finished_at,runtime_sec,"
                                   "exit_status,source) VALUES ('codex_cli',?,?,'codex_cli',?,?,?,'ok','backfill')",
                                   ("plan" if answer.parent.name.startswith("plan") else "review",
                                    answer.parent.name, int(t0), int(t1), round(t1 - t0, 1)))
        self.store.set_kv("runs_backfilled", now())

    def recover(self):
        """After a restart: threads are gone; a Claude process may still run and is adopted by the supervisor."""
        self.backfill_runs()
        for lease in self.store.query("SELECT * FROM leases WHERE state IN ('open','dispatched')"):
            job = self.store.job(lease["work_id"])
            if lease["agent"] == "claude" and job and job["status"] == "running":
                continue
            self.end_lease(lease["lease_id"], "interrupted", "supervisor restarted")
            if lease["agent"] == "gpt" and lease["task_type"] == "review" and job:  # bounded: blocked at 3
                self.store.execute("UPDATE jobs SET review_attempts=review_attempts+1 WHERE id=?", (job["id"],))

    def reconcile(self, _body: dict) -> tuple[int, dict]:
        with self.lock:
            expired = self.store.execute("UPDATE leases SET state='expired', ended=? WHERE state='open' AND "
                                         "expires<?", (now(), now()))
            lost = [r for r in self.store.query("SELECT * FROM leases WHERE state='dispatched' AND agent!='claude'")
                    if r["lease_id"] not in self.inflight]
            for r in lost:
                self.end_lease(r["lease_id"], "interrupted", "no live worker thread")
        self.sup.poll_claude()
        self.sup.expire_grok()
        est = {(e["provider"], e["task_type"]): e for e in estimates(self.store, self.cfg)}
        running = []
        for job in self.store.jobs("status='running'", limit=20):
            mdir = Path(job["mission_dir"] or "")
            files = [p.stat().st_mtime for p in mdir.rglob("*") if p.is_file()] if mdir.is_dir() else []
            progress = int(max(files, default=job["started"] or now()))
            e = est.get(("claude_code" if job["agent"] == "claude" else self.cfg.get("GROK_MODE"), job["kind"]), {})
            stall_after = max(self.cfg.int("STALL_AFTER_S"), int(1.5 * (e.get("p90_s") or 0)))
            stalled = now() - progress > stall_after
            if stalled and not job["status_reason"].startswith("suspected_stalled"):
                self.store.set_status(job["id"], "running", f"suspected_stalled: no file progress for "
                                      f"{now() - progress}s; not killed, hard deadline {job['deadline']}",
                                      expect=("running",))
            self.store.execute("UPDATE runs SET last_progress_at=? WHERE work_id=? AND finished_at IS NULL",
                               (progress, job["id"]))
            running.append({"job_id": job["id"], "agent": job["agent"], "elapsed_s": now() - (job["started"] or now()),
                            "eta_p50_s": e.get("p50_s"), "eta_p90_s": e.get("p90_s"),
                            "eta_confidence": e.get("confidence", "insufficient data (n=0)"),
                            "suspected_stalled": stalled, "hard_deadline": job["deadline"]})
        return 200, {"ok": True, "external_calls": False, "expired_leases": expired, "interrupted_leases": len(lost),
                     "running": running, "counts": self.store.counts()}

    # ------------------------------------------------------------ early alerts
    def notify_refusal(self, alert_id: int) -> str:
        rows = self.store.query("SELECT * FROM alerts WHERE id=?", (alert_id,))
        if not rows:
            return "unknown alert"
        a, cfg = rows[0], self.cfg
        if a["notified_at"]:
            return "already notified"
        if a["score"] < cfg.int("ALERT_NOTIFY_MIN_FLAGS"):
            return f"{a['score']} flags < ALERT_NOTIFY_MIN_FLAGS {cfg.get('ALERT_NOTIFY_MIN_FLAGS')}"
        if not cfg.live:
            return "dry run: a simulation never notifies"
        day = now() - now() % 86400
        if self.store.query("SELECT count(*) n FROM alerts WHERE notified_at>=?", (day,))[0]["n"] >= \
                cfg.int("ALERT_NOTIFY_MAX_DAY"):
            return "daily notification cap reached"
        if self.store.query("SELECT 1 FROM alerts WHERE address=? AND notified_at>?",
                            (a["address"], now() - cfg.int("ALERT_NOTIFY_COOLDOWN_S"))):
            return "cooldown for this account"
        return ""

    def notify(self, body: dict) -> tuple[int, dict]:
        alert_id = str(body.get("alert_id", ""))
        if not alert_id.isdigit():
            return 400, {"error": "alert_id"}
        with self.lock:
            refusal = self.notify_refusal(int(alert_id))
            if refusal:
                return 200, {"sent": False, "reason": refusal}
            a = self.store.query("SELECT * FROM alerts WHERE id=?", (int(alert_id),))[0]
            path = self.write_dossier(a)
            title = f"TriAgent {a['level']} alert, {a['score']} flags (NOT VERIFIED)"
            message = (f"{a['usdc']:,.0f} USDC by {a['address'][:10]}… on {a['condition_id'][:12]}…. Selection "
                       f"signal, not evidence of insider trading. Dossier: {path}")
            sent = self.notifier(title, message)
            if sent:
                self.store.execute("UPDATE alerts SET notified_at=? WHERE id=?", (now(), a["id"]))
            self.store.log("alert", f"notification {'sent' if sent else 'FAILED'} for alert {a['id']}")
        return 200, {"sent": sent, "dossier": str(path)}

    def write_dossier(self, a: dict) -> Path:
        prof = json.loads(a["features_json"])
        feat = prof.get("features", {})
        trades = self.store.query("SELECT tx_hash, ts, seen_at, side, outcome, usdc, price, title, onchain FROM trades "
                                  "WHERE proxy_wallet=? AND condition_id=? ORDER BY ts", (a["address"], a["condition_id"]))
        wallets = self.store.query("SELECT count(DISTINCT proxy_wallet) n, min(seen_at) since FROM trades")[0]
        alerts_n = self.store.query("SELECT count(*) n FROM alerts")[0]["n"]
        per_k = 1000 * alerts_n / wallets["n"] if wallets["n"] else None
        flags = json.loads(a["flags_json"])
        phase = "first fill (no earlier trade)" if feat.get("n_trades_before") == 0 else "later fill"
        lines = [
            f"# TriAgent alert {a['id']}: {a['level']}, NOT VERIFIED", "",
            "Selection signal from public data. It is not evidence of insider trading and not a trading signal.", "",
            f"- Observed (alert created): {iso(a['created'])}; trade event time: {iso(a['trade_ts'])} "
            f"(observed {a['created'] - a['trade_ts']} s after the trade)",
            f"- Market: `{a['condition_id']}` {trades[0]['title'] if trades else ''}",
            f"- Account (Polymarket proxy): `{a['address']}`; funders seen before the trade: {prof.get('funders')}",
            f"- Phase: {phase}; {a['usdc']:,.2f} USDC",
            f"- Criteria met ({a['score']} flags): " + "; ".join(f"{f}: {detector.FLAG_RULES.get(f, '?')}" for f in flags),
            f"- Point-in-time features (data observed before the trade only): `{canonical(feat)}`",
            f"- Data quality: activity truncated={prof.get('truncated')}, service labels "
            f"{'unavailable' if prof.get('service_labels') == 'unavailable' else 'checked'}, "
            f"feed at alert time {canonical(prof.get('feed_at_alert', 'not recorded'))}",
            f"- Base rate: no calibrated rate of insider trading exists. Observed alert load: {alerts_n} alerts among "
            f"{wallets['n']} wallets with a large trade collected since {iso(wallets['since'])}"
            + (f" ({per_k:.1f} per 1 000)." if per_k is not None else "."),
            "- Why this is not proof: large, fresh and concentrated trades are common for ordinary traders; shared "
            "bridges, exchanges and Polymarket contracts are services, not common ownership.",
            f"- Mission: {a['job_id'] or 'none (daily alert-mission cap reached)'}; dashboard http://127.0.0.1:"
            f"{self.cfg.get('HTTP_PORT')}/", "", "## Trades of this account in this market (event time, observed time)"]
        lines += [f"- {iso(t['ts'])} / {iso(t['seen_at'])} {t['side']} {t['outcome']} {t['usdc']:,.2f} USDC @ "
                  f"{t['price']} on-chain {t['onchain']}: https://polygonscan.com/tx/{t['tx_hash']}" for t in trades]
        lines += ["", f"Activity: https://data-api.polymarket.com/v2/activity?user={a['address']}&limit=100", ""]
        path = self.cfg.state_dir / "alerts" / f"alert-{a['id']}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text("\n".join(lines))
        return path

    # ------------------------------------------------------------ outbound events to n8n
    def send_pending(self, post=http) -> int:
        url, token = self.cfg.get("N8N_WAKE_URL"), self.cfg.secret("N8N_WAKE_TOKEN")
        if not (self.sup.n8n and url and token):
            self.store.execute("UPDATE bus SET sent_at=0, last_error='not routed: ORCHESTRATOR is not n8n' "
                               "WHERE sent_at IS NULL")
            return 0
        self.store.execute("UPDATE bus SET sent_at=0, last_error='expired unsent' WHERE sent_at IS NULL AND created<?",
                           (now() - 86400,))
        sent = 0
        for ev in self.store.query("SELECT * FROM bus WHERE sent_at IS NULL AND next_try<=? ORDER BY created LIMIT 20",
                                   (now(),)):
            try:
                post(url, method="POST", timeout=10, headers={self.cfg.get("N8N_WAKE_HEADER"): token},
                     body={"event_id": ev["event_id"], "event_type": ev["event_type"], "job_id": ev["job_id"],
                           "alert_id": ev["alert_id"], "emitted_at": ev["created"]})
                self.store.execute("UPDATE bus SET sent_at=? WHERE event_id=?", (now(), ev["event_id"]))
                sent += 1
            except ProviderError as exc:  # a resend keeps the event id: ingest stays idempotent
                n = ev["send_attempts"] + 1
                self.store.execute("UPDATE bus SET send_attempts=?, next_try=?, last_error=? WHERE event_id=?",
                                   (n, now() + min(900, 15 * 2 ** n), f"{exc.kind}: {exc}"[:300], ev["event_id"]))
                break  # n8n is down or refusing: do not hammer it
        return sent

    def bus_loop(self):
        while not self.sup.stop.is_set():
            try:
                self.send_pending()
            except Exception as exc:
                LOG.exception("bus")
                self.store.log("broker", f"event sender: {exc}", level="error")
            self.sup.stop.wait(3)


def iso(ts) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime(int(ts))) if ts else "unknown"


ROUTES = {"/v1/events/ingest": "ingest", "/v1/work/lease": "lease", "/v1/work/dispatch": "dispatch",
          "/v1/work/reconcile": "reconcile", "/v1/work/reject": "reject", "/v1/alerts/notify": "notify"}


def make_handler(broker: Broker):
    cfg = broker.cfg
    hosts = {f"127.0.0.1:{cfg.int('BROKER_PORT')}", f"localhost:{cfg.int('BROKER_PORT')}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # headers carry the token: never logged
            pass

        def send(self, code: int, body: dict):
            raw = json.dumps(body, default=str).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def authorized(self) -> bool:
            token = cfg.secret("BROKER_TOKEN")
            given = self.headers.get(cfg.get("BROKER_AUTH_HEADER")) or ""
            return bool(token) and hmac.compare_digest(given.encode(), token.encode())

        def do_GET(self):
            if self.headers.get("Host", "") not in hosts:
                return self.send(403, {"error": "host"})
            if not self.authorized():
                return self.send(401, {"error": "unauthorized"})
            if self.path == "/v1/work/estimates":
                return self.send(200, {"estimates": estimates(broker.store, cfg)})
            self.send(404, {"error": "not found"})

        def do_POST(self):
            if self.headers.get("Host", "") not in hosts:
                return self.send(403, {"error": "host"})
            if not self.authorized():
                return self.send(401, {"error": "unauthorized"})
            name = ROUTES.get(self.path)
            if not name:
                return self.send(404, {"error": "not found"})
            length = int(self.headers.get("Content-Length") or 0)
            if length > 65536:
                return self.send(413, {"error": "size"})
            try:
                body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            except json.JSONDecodeError:
                return self.send(400, {"error": "json"})
            if not isinstance(body, dict):
                return self.send(400, {"error": "not an object"})
            try:
                code, out = getattr(broker, name)(body)
            except Exception as exc:
                LOG.exception("broker %s", name)
                broker.store.log("broker", f"{name}: {exc}", level="error")
                code, out = 500, {"error": "internal"}
            self.send(code, out)

    return Handler
