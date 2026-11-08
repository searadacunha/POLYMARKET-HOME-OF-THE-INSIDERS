"""Read model of the Polymarket Investigation Center (port 8790) and its three operator commands.

Every view is a query on the existing SQLite memory, grouped by investigation; no view calls a model, so the
page works while Claude, GPT or Grok are down. The only network read is n8n's local /healthz, cached 30 s.
Commands (idea, pause/resume, preferences) are validated here and logged as `operator` events; the HTTP layer
authenticates them (service.make_handler).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import broker, detector, providers, reports
from .store import canonical, now
from .util import ProviderError, http

OPEN = ("queued", "running", "awaiting_external_result", "reviewing")
JOB_COLS = ("id,agent,kind,status,status_reason,task,falsifier,novelty,decision,investigation,origin,parent,depth,"
            "created,started,finished,updated,cost_usd,result_sha256,context_sha256,"
            "substr(json_extract(result_json,'$.report.summary'),1,1500) AS summary,"
            "json_extract(review_json,'$.analysis') AS analysis, json_extract(review_json,'$.enqueued') AS enqueued")
BRIDGE = re.compile(r"bridge|relay|debridge|across|stargate|cctp|wormhole|layerzero|hop protocol|socket|lifi|squid", re.I)
EXCHANGE = re.compile(r"exchange|binance|coinbase|kraken|okx|bybit|crypto\.com|kucoin|gate\.io|htx|huobi|mexc|bitget|"
                      r"changenow|fixedfloat", re.I)
_cache: dict[str, tuple[float, dict]] = {}


def in_list(values) -> str:
    return canonical(sorted(set(values)))


def n8n_health(cfg) -> dict:
    hit = _cache.get("n8n")
    if hit and time.time() - hit[0] < 30:
        return hit[1]
    try:
        http("http://127.0.0.1:5678/healthz", timeout=2)
        out = {"state": "ok", "text": "n8n répond (127.0.0.1:5678)"}
    except ProviderError as exc:
        out = {"state": "bad" if cfg.get("ORCHESTRATOR") == "n8n" else "warn", "text": f"n8n injoignable : {exc.kind}"}
    _cache["n8n"] = (time.time(), out)
    return out


def last_run(store, provider: str) -> dict:
    rows = store.query("SELECT task_type, work_id, started_at, finished_at, runtime_sec, exit_status FROM runs WHERE "
                       "provider=? ORDER BY id DESC LIMIT 1", (provider,))
    return rows[0] if rows else {}


def health(sup) -> dict:
    s, cfg = sup.store, sup.cfg
    out = {"n8n": n8n_health(cfg)}
    bus = s.query("SELECT max(sent_at) last FROM bus WHERE sent_at>0")[0]
    unsent = s.query("SELECT count(*) n, max(last_error) err FROM bus WHERE sent_at IS NULL")[0]
    out["n8n"]["events"] = {"last_sent": bus["last"], "unsent": unsent["n"], "last_error": unsent["err"] or ""}
    for name, agent, provider, run in (("Claude", "claude", "claude", "claude_code"),
                                       ("GPT (Codex)", "gpt", "openai", "codex_cli" if cfg.get("OPENAI_MODE") == "codex_cli" else "openai_api"),
                                       ("Grok", "grok", "xai", cfg.get("GROK_MODE"))):
        why = sup.held(provider) or providers.unavailable(cfg, agent)
        r = last_run(s, run)
        state = "bad" if why else ("warn" if r and r.get("exit_status") not in (None, "ok") else "ok")
        out[name] = {"state": state, "text": why or ("dernier passage " + (r.get("exit_status") or "en cours") if r else
                                                      "aucun passage enregistré"), "last_run": r}
    last = int(s.get_kv("last_collect_ok") or 0)
    age = now() - last if last else None
    out["Collecteur"] = {"state": "ok" if age is not None and age < 600 else ("warn" if age is not None and age < 3600 else "bad"),
                         "text": f"dernière collecte il y a {age // 60} min" if age is not None else "jamais collecté",
                         "feed": json.loads(s.get_kv("feed_status") or "{}")}
    acc = json.loads(s.get_kv("accounts_last") or "{}")
    if cfg.get("ACCOUNTS_SHADOW") == "1":
        a_age = now() - int(acc.get("at") or 0) if acc.get("at") else None
        out["Nouveaux comptes"] = {"state": "ok" if a_age is not None and a_age < 900 else "warn",
                                   "text": f"registre fantôme, passage il y a {a_age // 60} min" if a_age is not None else "aucun passage"}
    return out


def report_row(r: dict) -> dict:
    return {k: r[k] for k in ("id", "kind", "subject", "version", "investigation", "created", "period_start",
                              "period_end", "importance", "title", "sha256") if k in r}


# ---------------------------------------------------------------- pages
def home(sup, p: dict) -> dict:
    s = sup.store
    since = int(p.get("since") or 0) or now() - 86400
    count = lambda sql, *a: s.query(sql, a)[0]["n"]  # noqa: E731
    reps = s.query("SELECT * FROM reports WHERE created>? ORDER BY created DESC", (since,))
    latest_find = s.query("SELECT * FROM reports WHERE kind='mission' AND importance!='none' ORDER BY period_end DESC LIMIT 1")
    attention = [{"kind": "blocked", "text": f"{j['agent']} `{j['id'][:8]}` bloquée : {reports.flat(j['status_reason'], 200)}",
                  "route": f"investigations/{j['investigation']}", "ts": j["updated"]}
                 for j in s.query("SELECT * FROM jobs WHERE status='blocked' ORDER BY updated DESC LIMIT 10")]
    for prov in ("claude", "openai", "xai"):
        if sup.held(prov):
            attention.append({"kind": "hold", "text": f"{prov} en attente : {sup.held(prov)}", "route": "agents", "ts": now()})
    gate = sup.gate()
    if gate:
        attention.append({"kind": "gate", "text": f"Orchestration arrêtée : {gate}", "route": "commands", "ts": now()})
    threshold = sup.cfg.int("ALERT_NOTIFY_MIN_FLAGS")
    attention += [{"kind": "alert", "text": f"Alerte {a['level']} {a['id']} ({a['score']} indicateurs, signal non vérifié), "
                   f"{a['usdc']:,.0f} USDC", "route": f"alerts/{a['id']}", "ts": a["created"]}
                  for a in s.query("SELECT * FROM alerts WHERE status='new' AND (level='HIGH' OR score>=?) AND created>? "
                                   "ORDER BY created DESC LIMIT 10", (threshold, since))]
    attention += [{"kind": "notification", "text": n["title"] + " : " + n["message"], "route": n["link"].split("#/", 1)[-1],
                   "ts": n["created"]} for n in s.query("SELECT * FROM notifications WHERE created>? AND kind!='blocked' "
                                                         "ORDER BY created DESC LIMIT 5", (since,))]
    return {
        "now": now(), "since": since, "gate": gate or "running", "mode": sup.cfg.get("RUN_MODE"),
        "counts": {
            "missions_done": count("SELECT count(*) n FROM jobs WHERE status='done' AND finished>?", since),
            "missions_failed": count("SELECT count(*) n FROM jobs WHERE status IN ('failed','blocked') AND updated>?", since),
            "reports_major": len([r for r in reps if r["importance"] == "major"]),
            "reports_discovery": len([r for r in reps if r["importance"] != "none" and r["kind"] == "mission"]),
            "reports_empty": len([r for r in reps if r["importance"] == "none" and r["kind"] == "mission"]),
            "alerts_new": count("SELECT count(*) n FROM alerts WHERE created>?", since),
            "links_verified": count("SELECT count(*) n FROM edges WHERE job_id IS NOT NULL AND level='receipt_verified' "
                                    "AND created>?", since),
            "refuted": count("SELECT count(*) n FROM findings WHERE created>? AND (type='negative' OR tier='REFUTED')", since),
            "investigations_open": count("SELECT count(*) n FROM investigations WHERE status='open'"),
            "investigations_total": count("SELECT count(*) n FROM investigations"),
        },
        "latest_discovery": report_row(latest_find[0]) if latest_find else None,
        "latest_report": next((report_row(r) for r in s.query("SELECT * FROM reports ORDER BY period_end DESC, created DESC LIMIT 1")), None),
        "reports_since": [report_row(r) for r in reps[:10]],
        "attention": sorted(attention, key=lambda a: -int(a["ts"] or 0))[:15],
        "missions": s.query(f"SELECT {JOB_COLS} FROM jobs WHERE status IN (SELECT value FROM json_each(?)) "
                            "ORDER BY status='running' DESC, priority DESC, created LIMIT 20", (canonical(OPEN),)),
        "health": health(sup),
    }


def investigations(sup, _p: dict) -> dict:
    s = sup.store
    rows = s.query("""SELECT i.*, (SELECT count(*) FROM jobs j WHERE j.investigation=i.id) missions,
        (SELECT count(*) FROM jobs j WHERE j.investigation=i.id AND j.status IN ('queued','running','reviewing',
            'awaiting_external_result')) active,
        (SELECT max(novelty) FROM jobs j WHERE j.investigation=i.id) best_novelty,
        (SELECT count(*) FROM findings f WHERE f.investigation=i.id AND f.type='claim' AND f.tier IN ('CONFIRMED','SUPPORTED')) established,
        (SELECT count(*) FROM findings f WHERE f.investigation=i.id AND (f.type='negative' OR f.tier='REFUTED')) refuted,
        (SELECT id FROM reports r WHERE r.investigation=i.id ORDER BY period_end DESC LIMIT 1) last_report
        FROM investigations i ORDER BY i.updated DESC LIMIT 300""")
    for r in rows:
        r["origin"] = ("idée de l'opérateur" if r["id"].startswith("idea-") else
                       "alerte automatique" if r["title"].startswith("Automatic alert") else "directeur GPT")
    return {"triagent": rows,
            "repository": s.query("SELECT id, path, title, state, objective, conclusions, limits, scanned_at FROM inventory "
                                  "ORDER BY (id LIKE 'branch:%'), (id LIKE 'note:%'), id")}


def investigation(sup, p: dict) -> dict:
    s, inv_id = sup.store, str(p.get("id", ""))
    inv = s.investigation(inv_id)
    if not inv:
        return {"error": "unknown investigation"}
    jobs = s.query(f"SELECT {JOB_COLS} FROM jobs WHERE investigation=? ORDER BY created", (inv_id,))
    ids = in_list(j["id"] for j in jobs)
    alerts = s.query("SELECT id, address, condition_id, level, score, usdc, trade_ts, status FROM alerts WHERE job_id IN "
                     "(SELECT value FROM json_each(?))", (ids,))
    return {
        "investigation": inv, "jobs": jobs, "alerts": alerts,
        "idea": next(iter(s.query("SELECT * FROM ideas WHERE investigation=?", (inv_id,))), None),
        "findings": s.query("SELECT id, investigation, job_id, type, text, tier, evidence_json, created FROM findings WHERE investigation=? "
                            "ORDER BY id", (inv_id,)),
        "reports": [report_row(r) for r in s.query("SELECT * FROM reports WHERE investigation=? ORDER BY period_end DESC", (inv_id,))],
        "edges": s.query("SELECT * FROM edges WHERE job_id IN (SELECT value FROM json_each(?)) ORDER BY ts", (ids,)),
        "evidence": s.query("SELECT sha256, source, ref, chain, fetched_at, bytes, job_id FROM evidence WHERE job_id IN "
                            "(SELECT value FROM json_each(?)) ORDER BY fetched_at LIMIT 500", (ids,)),
        "wallets": s.query("SELECT address, first_seen, examined_by FROM wallets WHERE examined_by IN "
                           "(SELECT value FROM json_each(?)) ORDER BY first_seen", (ids,)),
    }


def alert_view(s, a: dict) -> dict:
    job = s.job(a["job_id"]) if a["job_id"] else None
    claims = json.loads(job["review_json"]).get("claims", []) if job and job["review_json"] else []
    tiers = {c.get("tier") for c in claims}
    a["proof"] = ("résultat confirmé" if "CONFIRMED" in tiers else "revu : étayé, non confirmé" if "SUPPORTED" in tiers
                  else "revu : non établi" if job and job["review_json"] else "signal non vérifié")
    a["investigation"] = job["investigation"] if job else None
    a["job_status"] = job["status"] if job else None
    a["decision"] = job["decision"] if job else None
    a["flags"] = json.loads(a.pop("flags_json") or "[]")
    return a


def alerts(sup, _p: dict) -> dict:
    s = sup.store
    rows = s.query("""SELECT a.id, a.created, a.address, a.condition_id, a.trade_ts, a.usdc, a.score, a.level, a.status,
        a.job_id, a.notified_at, a.flags_json, (SELECT title FROM trades t WHERE t.condition_id=a.condition_id LIMIT 1) market
        FROM alerts a ORDER BY a.created DESC LIMIT 300""")
    return {"alerts": [alert_view(s, a) for a in rows], "flag_rules": detector.FLAG_RULES,
            "notify_min_flags": sup.cfg.int("ALERT_NOTIFY_MIN_FLAGS")}


def alert(sup, p: dict) -> dict:
    s = sup.store
    rows = s.query("SELECT * FROM alerts WHERE id=?", (int(p.get("id") or 0),))
    if not rows:
        return {"error": "unknown alert"}
    a = rows[0]
    prof = json.loads(a.pop("features_json") or "{}")
    view = alert_view(s, a)
    job = s.job(a["job_id"]) if a["job_id"] else None
    review = json.loads(job["review_json"]) if job and job["review_json"] else {}
    report = json.loads(job["result_json"]).get("report", {}) if job and job["result_json"] else {}
    alternatives = [x for f in report.get("findings", []) for x in f.get("alternative_explanations", [])]
    dossier = sup.cfg.state_dir / "alerts" / f"alert-{a['id']}.md"
    return {
        "alert": view, "features": prof.get("features", {}), "funders": prof.get("funders"),
        "service_labels": prof.get("service_labels"), "truncated": prof.get("truncated"),
        "feed_at_alert": prof.get("feed_at_alert"), "flag_rules": {f: detector.FLAG_RULES.get(f, "?") for f in view["flags"]},
        "flags_total": len(detector.FLAG_RULES),
        "fills": s.query("SELECT tx_hash, ts, seen_at, side, outcome, usdc, price, title, onchain FROM trades WHERE "
                         "proxy_wallet=? AND condition_id=? ORDER BY ts", (a["address"], a["condition_id"])),
        "edges": s.query("SELECT e.*, v.ref evidence_ref FROM edges e LEFT JOIN evidence v ON v.sha256=e.evidence_sha256 "
                         "WHERE (e.src=? OR e.dst=?) AND e.level='receipt_verified' ORDER BY e.ts LIMIT 200",
                         (a["address"], a["address"])),
        "claims": review.get("claims", []), "alternatives": alternatives[:20], "review_analysis": review.get("analysis"),
        "report_id": next((r["id"] for r in s.query("SELECT id FROM reports WHERE subject=? ORDER BY version DESC", (a["job_id"],))), None),
        "dossier": str(dossier) if dossier.is_file() else None,
    }


def classify(address: str, tags: list, alerted: set) -> str:
    text = " ".join(tags)
    if address in alerted:
        return "alert"
    if BRIDGE.search(text):
        return "bridge"
    if EXCHANGE.search(text):
        return "exchange"
    return "service" if tags else "wallet"


def graph(sup, p: dict) -> dict:
    """Edges of one investigation, of one address, or (default) every mission edge plus the alerted accounts'
    funding and exits. Parallel edges between two addresses are grouped; each keeps its transaction and evidence."""
    s = sup.store
    cols = "e.*, v.ref evidence_ref, v.source evidence_source"
    base = f"SELECT {cols} FROM edges e LEFT JOIN evidence v ON v.sha256=e.evidence_sha256"
    alerted = {r["address"] for r in s.query("SELECT DISTINCT address FROM alerts")}
    if p.get("address"):
        a = str(p["address"]).lower()
        rows = s.query(f"{base} WHERE e.src=? OR e.dst=? ORDER BY e.ts DESC LIMIT 600", (a, a))
    elif p.get("inv"):
        jobs = in_list(r["id"] for r in s.query("SELECT id FROM jobs WHERE investigation=?", (p["inv"],)))
        addrs = in_list(r["address"] for r in s.query("SELECT address FROM alerts WHERE job_id IN (SELECT value FROM "
                                                      "json_each(?))", (jobs,)))
        rows = s.query(f"{base} WHERE e.job_id IN (SELECT value FROM json_each(?)) OR e.src IN (SELECT value FROM "
                       f"json_each(?)) OR e.dst IN (SELECT value FROM json_each(?)) ORDER BY e.ts DESC LIMIT 600",
                       (jobs, addrs, addrs))
    else:
        rows = s.query(f"{base} WHERE e.job_id IS NOT NULL OR e.src IN (SELECT address FROM alerts) OR e.dst IN "
                       f"(SELECT address FROM alerts) ORDER BY e.ts DESC LIMIT 600")
    addrs = {r["src"] for r in rows} | {r["dst"] for r in rows}
    labels = {r["address"]: json.loads(r["tags_json"]) for r in s.query(
        "SELECT address, tags_json FROM labels WHERE address IN (SELECT value FROM json_each(?))", (in_list(addrs),))}
    nodes = {a: {"id": a, "type": classify(a, labels.get(a, []), alerted), "tags": labels.get(a, []), "degree": 0}
             for a in addrs}
    links: dict[tuple, dict] = {}
    for r in rows:
        kinds = {nodes[r["src"]]["type"], nodes[r["dst"]]["type"]}
        cat = ("hypothesis" if r["kind"] in ("HYPOTHESIS", "TEMPORAL_CORRELATION") else
               "bridge" if r["kind"] == "BRIDGE_ORDER" or "bridge" in kinds else
               "exchange" if "exchange" in kinds else
               "service" if r["kind"] == "SHARED_SERVICE" or "service" in kinds else
               "shared" if r["kind"] in ("SAME_FUNDER", "SAME_DEPOSIT_ADDRESS") else "direct")
        key = (r["src"], r["dst"], cat)
        link = links.setdefault(key, {"src": r["src"], "dst": r["dst"], "category": cat, "verified": False, "tx": []})
        link["verified"] |= r["level"] == "receipt_verified"
        link["tx"].append({k: r[k] for k in ("kind", "level", "chain", "tx_hash", "token", "amount", "ts", "method",
                                             "evidence_sha256", "evidence_ref", "evidence_source", "job_id")}
                          | {"amount_text": reports.amount(r)})
    for link in links.values():
        nodes[link["src"]]["degree"] += 1
        nodes[link["dst"]]["degree"] += 1
    return {"nodes": list(nodes.values()), "links": list(links.values()), "truncated": len(rows) >= 600}


def agents(sup, _p: dict) -> dict:
    s, cfg = sup.store, sup.cfg
    day = providers.day_start()
    caps = {"claude": ("CLAUDE_MAX_USD_DAY", "CLAUDE_MAX_MISSIONS_DAY"), "openai": ("OPENAI_MAX_USD_DAY", "OPENAI_MAX_CALLS_DAY"),
            "xai": ("XAI_MAX_USD_DAY", "GROK_MAX_MISSIONS_DAY")}
    why, _ = broker.Broker(sup).availability()  # local only: holds, budgets, leases, binaries
    out = []
    for agent, provider, label, mode, runs in (
            ("claude", "claude", "Claude Code (recherche on-chain)", cfg.get("CLAUDE_AUTH") + " · " + cfg.get("CLAUDE_MODEL"), ("claude_code",)),
            ("gpt", "openai", "GPT via Codex CLI (directeur scientifique)", cfg.get("OPENAI_MODE") + " · " + (cfg.get("CODEX_MODEL") or "modèle Codex par défaut"), ("codex_cli", "openai_api")),
            ("grok", "xai", "Grok (historique X)", cfg.get("GROK_MODE"), (cfg.get("GROK_MODE"), "grok_cli", "xai_api", "bot"))):
        usd, calls = s.spent(provider, day)
        lease = s.query("SELECT work_id, task_type, created, state FROM leases WHERE agent=? AND state IN ('open','dispatched') "
                        "ORDER BY created DESC LIMIT 1", (agent,))
        job_agent = {"gpt": None}.get(agent, agent)
        working = s.query(f"SELECT {JOB_COLS} FROM jobs WHERE agent=? AND status IN ('running','awaiting_external_result')",
                          (job_agent,)) if job_agent else []
        out.append({
            "agent": agent, "label": label, "mode": mode, "hold": sup.held(provider),
            "blocker": why.get(agent, "") or providers.unavailable(cfg, agent),
            "lease": lease[0] if lease else None, "working": working,
            "spend": {"usd": round(usd, 2), "calls": calls, "usd_cap": cfg.get(caps[provider][0]), "calls_cap": cfg.get(caps[provider][1])},
            "runs": s.query("SELECT task_type, work_id, started_at, finished_at, runtime_sec, exit_status FROM runs WHERE "
                            "provider IN (SELECT value FROM json_each(?)) ORDER BY id DESC LIMIT 8", (in_list(runs),)),
        })
    return {"agents": out, "durations": broker.estimates(s, cfg), "health": health(sup),
            "awaiting_review": s.query(f"SELECT {JOB_COLS} FROM jobs WHERE status='reviewing' ORDER BY updated"),
            "leases": s.query("SELECT work_id, agent, task_type, state, created, ended, outcome FROM leases ORDER BY created "
                              "DESC LIMIT 20"),
            "orchestrator": cfg.get("ORCHESTRATOR"), "gate": sup.gate() or "running"}


def report_list(sup, p: dict) -> dict:
    where, args = ["1=1"], []
    for key, col in (("inv", "investigation"), ("importance", "importance"), ("kind", "kind")):
        if p.get(key):
            where.append(f"{col}=?")
            args.append(str(p[key]))
    for key, op in (("from", ">="), ("to", "<")):
        if p.get(key):
            try:
                ts = int(time.mktime(time.strptime(str(p[key]), "%Y-%m-%d"))) + (86400 if key == "to" else 0)
            except ValueError:
                return {"error": f"{key}: YYYY-MM-DD"}
            where.append(f"coalesce(period_end, created){op}?")
            args.append(ts)
    rows = sup.store.query(f"SELECT * FROM reports WHERE {' AND '.join(where)} ORDER BY period_end DESC, created DESC LIMIT 500", args)
    return {"reports": [report_row(r) for r in rows],
            "investigations": sup.store.query("SELECT DISTINCT r.investigation id, i.title FROM reports r JOIN investigations "
                                              "i ON i.id=r.investigation ORDER BY i.updated DESC")}


def report(sup, p: dict) -> dict:
    rows = sup.store.query("SELECT * FROM reports WHERE id=?", (str(p.get("id", "")),))
    if not rows:
        return {"error": "unknown report"}
    r = rows[0]
    r["versions"] = sup.store.query("SELECT id, version, created, sha256 FROM reports WHERE kind=? AND subject=? ORDER BY version",
                                    (r["kind"], r["subject"]))
    return r


def report_markdown(sup, rid: str) -> tuple[str, bytes] | None:
    r = report(sup, {"id": rid})
    if "error" in r:
        return None
    trailer = (f"\n\n---\nReport `{r['id']}`, version {r['version']}, created {reports.iso(r['created'])}. "
               f"SHA-256 of the report body above (UTF-8, without this trailer): `{r['sha256']}`\n")
    return f"{r['id']}.md", (r["body_md"] + trailer).encode()


def ideas(sup, _p: dict) -> dict:
    s = sup.store
    out = []
    for i in s.query("SELECT * FROM ideas ORDER BY id DESC LIMIT 100"):
        i["decision"] = json.loads(i.pop("decision_json") or "null")
        i["jobs"] = s.query("SELECT id, agent, kind, status, task, falsifier, novelty, decision FROM jobs WHERE "
                            "investigation=? ORDER BY created", (i["investigation"],))
        out.append(i)
    return {"ideas": out, "paused": s.get_kv("paused") == "1", "gate": sup.gate() or "running",
            "orchestrator": sup.cfg.get("ORCHESTRATOR")}


def prefs(sup, _p: dict) -> dict:
    return {"prefs": {k: reports.pref(sup.store, sup.cfg, k) for k in reports.PREFS},
            "defaults": {k: sup.cfg.get(k) for k in reports.PREFS},
            "commands_enabled": bool(sup.cfg.secret("UI_TOKEN")),
            "notifications": sup.store.query("SELECT * FROM notifications ORDER BY created DESC LIMIT 30")}


def raw(sup, p: dict) -> dict:
    """Audit view: rows of one table as stored (bounded); the original evidence files stay on disk."""
    table = str(p.get("table", ""))
    if table not in ("jobs", "investigations", "findings", "evidence", "edges", "alerts", "runs", "events", "reports",
                     "notifications", "ideas", "leases", "bus", "inventory"):
        return {"error": "unknown table"}
    return {"table": table, "rows": sup.store.query(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 200")}


GET = {"home": home, "investigations": investigations, "investigation": investigation, "alerts": alerts, "alert": alert,
       "graph": graph, "agents": agents, "reports": report_list, "report": report, "ideas": ideas, "prefs": prefs,
       "raw": raw}


# ---------------------------------------------------------------- commands (authenticated by the HTTP layer)
def submit_idea(sup, body: dict) -> tuple[int, dict]:
    text = " ".join(str(body.get("text", "")).split())
    if not 15 <= len(text) <= 2000:
        return 400, {"error": "l'idée doit faire entre 15 et 2000 caractères"}
    s = sup.store
    with s.conn(immediate=True) as c:
        n = c.execute("SELECT coalesce(max(id),0)+1 FROM ideas").fetchone()[0]
        inv = f"idea-{n}"
        c.execute("INSERT INTO investigations(id,title,created,updated) VALUES (?,?,?,?)",
                  (inv, ("Idée de l'opérateur : " + text)[:300], now(), now()))
        c.execute("INSERT INTO ideas(id,created,text,investigation) VALUES (?,?,?,?)", (n, now(), text, inv))
    s.log("operator", f"idea {n} submitted from the dashboard: {text[:300]}")
    s.emit("work.ready", job_id=inv)  # wakes n8n; the broker leases it to GPT when GPT is free
    return 200, {"idea": n, "investigation": inv}


def control(sup, body: dict) -> tuple[int, dict]:
    action = body.get("action")
    if action not in ("pause", "resume"):
        return 400, {"error": "action: pause | resume"}
    sup.store.set_kv("paused", "1" if action == "pause" else "0")
    sup.store.log("operator", f"orchestration {action}d from the dashboard")
    if action == "resume":
        sup.store.emit("work.ready", job_id="resume")
    return 200, {"paused": action == "pause"}


def set_prefs(sup, body: dict) -> tuple[int, dict]:
    if not body or any(k not in reports.PREFS or not isinstance(v, str) or not reports.PREFS[k](v) for k, v in body.items()):
        return 400, {"error": "invalid preference", "allowed": list(reports.PREFS)}
    for k, v in body.items():
        sup.store.set_kv("pref." + k, v)
    sup.store.log("operator", f"preferences changed from the dashboard: {canonical(body)}")
    return 200, {"prefs": {k: reports.pref(sup.store, sup.cfg, k) for k in reports.PREFS}}


POST = {"idea": submit_idea, "control": control, "prefs": set_prefs}


def ui_page(code_dir: Path, nonce: str) -> bytes:
    return (code_dir / "triagent" / "ui.html").read_bytes().replace(b"<script>", f'<script nonce="{nonce}">'.encode())
