"""Persistent historical campaign: lead registry, coverage grid, GPT triage and audit, passes and saturation.

Grok searches one cell of a coverage grid (topic x period) per fresh session; the supervisor re-reads every cited post
and registers each lead once (unique dedup key). GPT triages new leads in fresh, short-context sessions: a bounded
Claude mission, one X follow-up, a duplicate, a closure with its reason, or a deferral. Claude missions keep the
existing GPT review. A dossier with a significant supported or confirmed result is audited by GPT, then published as
a draft PR by publish.py. A pass ends when every cell has been searched and nothing is pending; two consecutive
passes without a significant result end the campaign (saturation of the defined scope, not of insider trading).
Everything lives in SQLite: a restart or a new AI session resumes from the tables, never from a conversation.
"""
from __future__ import annotations

import calendar
import csv
import hashlib
import json
import re
import time
from pathlib import Path

from . import inventory, providers, schemas
from .config import Config
from .store import Store, canonical, normalize_key, now
from .util import ProviderError

TOPICS = {
    "insider": "insider trading, informed trading or suspicious bets on Polymarket",
    "wallets": "specific suspicious Polymarket wallets or accounts named publicly (addresses, profiles, transactions)",
    "pre_announcement": "unusual Polymarket bets placed shortly before an official announcement, leak or publication",
    "coordination": "manipulation, wash trading or coordination between Polymarket accounts",
    "geopolitics": "Polymarket bets on military strikes, wars, ceasefires and other geopolitical events",
    "politics": "Polymarket bets on elections, appointments, pardons, court rulings and government decisions",
    "sports_awards": "Polymarket bets on sports results, transfers and awards (Ballon d'Or, Oscars, Nobel, Grammys)",
    "corporate": "Polymarket bets on company, product, earnings, technology or entertainment announcements",
}
PERIODS = ("2026", "2025", "2024", "2023", "2020-2022")  # recent first: more chain data, more value for the detector
LANGUAGES = "English, Spanish, French, Portuguese, German, Russian, Chinese, Korean, Hebrew, Persian, Arabic, Turkish"
OPEN_JOB = "('queued','running','awaiting_external_result','reviewing')"
POST = re.compile(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status(?:es)?/(\d{5,25})")
EVM = re.compile(r"^0x[0-9a-fA-F]{40}$")
TX = re.compile(r"^(0x[0-9a-fA-F]{64}|[1-9A-HJ-NP-Za-km-z]{64,90})$")
SOL = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
WEIGHTS = {"source_quality": 1, "verifiable_transactions": 2, "amount": 1, "unusual_timing": 1,
           "financial_connections": 2, "originality": 1.5, "refutability": 1, "detector_value": 1, "cost": -1}
CLAUDE_CHECKLIST = """
Reconstruct, for each account in scope, from primary data only (tg-fetch archives every response):
- BEFORE the first bet: origin of the funds, intermediate wallets, first activity and first deposit, swaps or bridges
  used (Relay, deBridge, CCTP, ChangeNOW-like services), grouped funding, other accounts funded by the same sources,
  delay between funding and the first position.
- DURING: first executed position, amounts, liquidity and price history around it, coordinated positions or
  synchronized reversals, volume and concentration, real exposure, comparison with ordinary traders of the same market
  (a representative comparator, never only the biggest winners).
- AFTER: reconciled result, withdrawals, destination wallets, cross-chain bridges, swap services, exchange deposit
  addresses, reuse of destinations, connections to other accounts.
Polygon first; Ethereum, TRON, Base, Solana, BSC or Arbitrum only where the funds actually go. Record DIRECT_TRANSFER,
BRIDGE_ORDER (with the protocol order id), SAME_DEPOSIT_ADDRESS (exchange deposit) and TEMPORAL_CORRELATION as
separate edges, each with its transaction and time. An exchange address is not an identity nor common control.
Never invent a missing transaction: say it is missing. Every financial statement needs an evidence id and the method
to re-check it. In methods_used, record the first bet as method 'timeline:first_trade' (window_start = its unix time)
and the triggering event or announcement as 'timeline:event' when known.
"""
TRIAGER = providers.DIRECTOR + """
You now triage leads of a historical campaign (posts on X, cases already in the repository, wallets, gaps). For each
lead given, return exactly one decision with its lead_id unchanged:
- investigate: a Claude Code on-chain mission is worth it (addresses, transactions, a market and a time window can be
  checked). Write a bounded task (named accounts, market, window) and a concrete falsifier; novelty_key must be new.
- x_followup: the post lacks checkable elements but its thread, replies or quotes probably carry them (Grok, once).
- duplicate: same case as another lead (duplicate_of = its id) or as a repository investigation.
- close_already_investigated / close_no_verifiable_element / close_noise: say why in reason.
- defer: plausible but too costly or blocked now.
A post is a lead, never proof of insider trading. Look for innocent explanations (public news, hedging, market
makers, copy trading, shared services). Biggest winners are not insiders by default. Score each lead 0-5 on every
criterion (cost: 5 = very expensive). You may also return at most two `gaps`: material holes of the repository itself
that no lead covers, as bounded missions. Return nothing to launch when nothing is worth it."""
AUDITOR = providers.DIRECTOR + """
You now audit a finished campaign dossier before publication in a public research repository. Keep only claims whose
evidence ids are listed in EVIDENCE INDEX (or repo:<path>) and whose tier the data supports; demote the others.
Separate a direct transfer, a verified bridge order, an exchange deposit and a mere correlation. List innocent
explanations, limits and what is NOT demonstrated (identity, common ownership, inside information unless proven).
Give the first bet time and the event time in UTC (ISO 8601) or an empty string when unknown. publishable = true only
when at least one SUPPORTED or CONFIRMED financial fact is new relative to the repository inventory."""


# ---------------------------------------------------------------- registry
def lead_id(key: str) -> str:
    return "L-" + hashlib.sha256(normalize_key(key).encode()).hexdigest()[:10]


def current_pass(store: Store) -> int:
    return int(store.get_kv("campaign.pass") or 1)


def add_lead(store: Store, key: str, kind: str, title: str, *, state: str = "new", **fields) -> tuple[str, bool]:
    """Insert once per dedup key; returns (id, inserted)."""
    key = normalize_key(key)
    lid = lead_id(key)
    cols = {"id": lid, "dedup_key": key, "kind": kind, "title": " ".join(str(title).split())[:300] or key,
            "state": state, "pass": current_pass(store), "created": now(), "updated": now(), **fields}
    for k in ("sources_json", "addresses_json", "txs_json", "score_json"):
        if k in cols and not isinstance(cols[k], str):
            cols[k] = canonical(cols[k])
    n = store.execute(f"INSERT OR IGNORE INTO leads({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                      list(cols.values()))
    return lid, bool(n)


def update_lead(store: Store, lid: str, **fields):
    for k in ("sources_json", "addresses_json", "txs_json", "score_json"):
        if k in fields and not isinstance(fields[k], str):
            fields[k] = canonical(fields[k])
    fields["updated"] = now()
    store.execute(f"UPDATE leads SET {','.join(f'{k}=?' for k in fields)} WHERE id=?", [*fields.values(), lid])


def priority(scores: dict) -> int:
    """1-5 from the nine criteria (weights above); cost lowers it. Deterministic, so GPT cannot inflate it alone."""
    lo = sum(5 * w for w in WEIGHTS.values() if w < 0)
    hi = sum(5 * w for w in WEIGHTS.values() if w > 0)
    s = sum(w * max(0, min(5, int(scores.get(k, 0)))) for k, w in WEIGHTS.items())
    return max(1, min(5, round(1 + 4 * (s - lo) / (hi - lo))))


def parse_utc(text) -> int | None:
    text = str(text or "").strip().replace(" ", "T")
    for fmt, n in (("%Y-%m-%dT%H:%M:%S", 19), ("%Y-%m-%dT%H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return calendar.timegm(time.strptime(text[:n], fmt))
        except ValueError:
            continue
    return None


def split_ids(values) -> tuple[list[str], list[str]]:
    addrs, txs = set(), set()
    for v in values or []:
        v = str(v).strip()
        if EVM.match(v):
            addrs.add(v.lower())
        elif TX.match(v):
            txs.add(v.lower() if v.startswith("0x") else v)
        elif SOL.match(v):
            addrs.add(v)
    return sorted(addrs), sorted(txs)


# ---------------------------------------------------------------- seeding from the repository
SEED_FILES = ("research_notes/x-history-2026-11-06/LEADS.csv",
              "research_notes/x-corpus-reconciliation-2026-11-06/ADJUDICATION.csv",
              "research_notes/external-polymarket-cases-2026-11-07/CASES.csv",
              "research_notes/kpmg-election-integrity-2026-11-07/CASES.csv")
STATUS_FILE = "research_notes/x-history-2026-11-06/verification/LEADS_STATUS.csv"
SETTLED = ("CONFIRMED", "SUPPORTED", "REFUTED", "VERIFIED")


def seed(cfg: Config, store: Store) -> dict:
    """Known cases (inventory) are registered closed: they are the memory against repetition. Leads and cases of the
    repository's intake notes are registered new unless their verification already settled them."""
    out = {"known_cases": 0, "repo_leads": 0, "settled": 0}
    for r in store.query("SELECT id, path, title, state, conclusions FROM inventory"):
        _, added = add_lead(store, f"case:inv:{r['id']}", "known_case", r["title"] or r["id"], state="closed",
                            owner="none", source_ref=r["path"], hypothesis=(r["conclusions"] or "")[:1500],
                            closure_reason=f"repository investigation ({r['state']}): {r['path']}")
        out["known_cases"] += added
    status = {}
    path = cfg.repo_dir / STATUS_FILE
    if path.is_file():
        status = {row["lead_id"]: row for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines())}
    for rel in SEED_FILES:
        path = cfg.repo_dir / rel
        if not path.is_file():
            continue
        for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines()):
            rid = row.get("lead_id") or row.get("case_id") or row.get("id") or ""
            url = row.get("source") or row.get("source_url") or row.get("primary_source_url") or ""
            m = POST.search(url)
            pid = row.get("post_id") or (m.group(2) if m else "")
            addrs, txs = split_ids([row.get("candidate_proxy_or_destination"), (status.get(rid) or {}).get("resolved_address")])
            key = f"x:{pid}" if pid else (f"addr:{addrs[0]}" if addrs else f"case:{rel}:{rid}")
            title = " — ".join(x for x in (row.get("case") or row.get("theme") or row.get("category") or "",
                                           row.get("reported_claim") or row.get("source_claim") or row.get("subject")
                                           or row.get("reported_amount_or_result") or "") if x)
            verdict = (status.get(rid) or {}).get("status") or row.get("source_status") or row.get("status") or ""
            settled = verdict.upper().startswith(SETTLED)
            sources = [{"url": url, "post_id": pid, "author": m.group(1) if m else "",
                        "created_at": row.get("event_time_utc") or row.get("observed_time_utc") or "",
                        "verified": None, "first_hand": None, "text": ""}] if url else []
            _, added = add_lead(store, key, "x_post" if pid else ("wallet" if addrs else "known_case"), title,
                                state="closed" if settled else "new", owner="none" if settled else "gpt",
                                source_ref=f"{rel}#{rid}", sources_json=sources, addresses_json=addrs, txs_json=txs,
                                hypothesis=(row.get("reported_claim") or row.get("source_claim") or "")[:1500],
                                checks=(row.get("required_test") or row.get("next_test") or
                                        row.get("next_required_test") or "")[:1000] + f" [repository status: {verdict}]",
                                closure_reason=f"settled in the repository: {verdict} ({rel})" if settled else "")
            out["repo_leads"] += added
            out["settled"] += added and settled
    store.log("campaign", f"seeded {canonical(out)}")
    return out


# ---------------------------------------------------------------- control
def state(store: Store) -> str:
    return store.get_kv("campaign.state") or "off"


def start(cfg: Config, store: Store) -> dict:
    if state(store) == "saturated":
        return {"state": "saturated", "note": "already saturated; `triagent campaign reopen` starts a new pass"}
    store.set_kv("campaign.state", "running")
    store.execute("INSERT OR IGNORE INTO passes(n, started) VALUES (?, ?)", (current_pass(store), now()))
    store.set_kv("campaign.pass", current_pass(store))
    out = seed(cfg, store)
    out["resumed_jobs"] = store.execute("UPDATE jobs SET status='queued', status_reason='campaign resumed', updated=? "
                                        "WHERE origin='campaign' AND status='paused'", (now(),))
    store.log("campaign", f"campaign running, pass {current_pass(store)}")
    store.emit("work.ready", job_id="campaign")
    return {"state": "running", "pass": current_pass(store), **out}


def stop(store: Store, reason: str = "operator") -> int:
    """No new cell, triage or audit; queued campaign missions are paused (kept, never deleted) until `start`."""
    store.set_kv("campaign.state", "stopped")
    paused = store.execute("UPDATE jobs SET status='paused', status_reason=?, updated=? WHERE origin='campaign' AND "
                           "status='queued'", (f"campaign stopped ({reason}); `triagent campaign start` requeues it", now()))
    store.log("campaign", f"campaign stopped: {reason}; {paused} queued mission(s) paused")
    return paused


def reopen(store: Store) -> int:
    """After saturation, a new source or method justifies one more pass (an operator decision)."""
    n = current_pass(store) + 1
    store.execute("INSERT OR IGNORE INTO passes(n, started) VALUES (?, ?)", (n, now()))
    store.set_kv("campaign.pass", n)
    store.set_kv("campaign.state", "running")
    store.log("campaign", f"campaign reopened by the operator: pass {n}")
    return n


# ---------------------------------------------------------------- Grok cells
def next_cell(store: Store, n: int) -> str | None:
    done = {r["cell"] for r in store.query("SELECT cell FROM searches WHERE pass=?", (n,))}
    return next((f"{t}:{p}" for p in PERIODS for t in TOPICS if f"{t}:{p}" not in done), None)


def cell_task(store: Store, n: int, cell: str) -> str:
    topic, period = cell.split(":", 1)
    seen = [r["dedup_key"][2:] for r in store.query(
        "SELECT dedup_key FROM leads WHERE topic=? AND period=? AND dedup_key LIKE 'x:%' LIMIT 80", (topic, period))]
    return (f"Historical campaign, pass {n}, cell {cell}. Search X for public posts about {TOPICS[topic]}, "
            f"published in {period}. Search in several languages ({LANGUAGES}), with several phrasings, and follow "
            f"replies, quote posts and threads. Prefer posts that give Polymarket wallet addresses, transaction hashes, "
            f"market names, timestamps or documents that can be checked on chain; skip reposts, memes and accusations "
            f"without a checkable element. Put the market and the event in `claim`, and every address and transaction "
            f"cited in `addresses` and `transactions`. Return at most 15 leads, original posts only."
            + (f" These post ids are already registered, return other posts: {', '.join(seen)}." if seen else "")
            + (" This is a later, independent pass: use other phrasings and languages than a first search would."
               if n > 1 else ""))


def enqueue_cell(store: Store, n: int, cell: str) -> str | None:
    store.ensure_investigation(f"camp-grid-p{n}", f"Campaign pass {n}: X search grid")
    jid = store.enqueue("grok", "x_research", f"campaign pass {n} cell {cell}", cell_task(store, n, cell),
                        origin="campaign", investigation=f"camp-grid-p{n}", falsifier="A lead whose post cannot be "
                        "re-read, or whose claim has no checkable element, is closed, not investigated.", priority=2)
    if jid:
        topic, period = cell.split(":", 1)
        store.execute("INSERT OR IGNORE INTO searches(job_id,cell,topic,period,pass,created) VALUES (?,?,?,?,?,?)",
                      (jid, cell, topic, period, n, now()))
    return jid


def ingest_grok(cfg: Config, store: Store, job: dict, verify=providers.verify_x_leads) -> dict:
    """No model call: the supervisor re-reads each cited post, then registers each lead once."""
    report = json.loads(job["result_json"])["report"]
    leads = [x for x in report.get("leads", []) if isinstance(x, dict)][:40]
    checks = verify(leads) if cfg.live else []
    by_post = {c["post_id"]: c for c in checks}
    cell = (store.query("SELECT topic, period FROM searches WHERE job_id=?", (job["id"],)) or [{"topic": "", "period": ""}])[0]
    parent = store.query("SELECT * FROM leads WHERE job_id=?", (job["id"],))
    known = {r["address"].lower() for r in store.query("SELECT address FROM known_addresses")}
    new, dup, verified, ids = 0, 0, 0, []
    for x in leads:
        url = str(x.get("post_url", ""))[:300]
        m = POST.search(url)
        pid = str(x.get("post_id") or (m.group(2) if m else ""))
        chk = by_post.get(pid, {})
        claim = " ".join(str(x.get("claim", "")).split())
        key = f"x:{pid}" if pid.isdigit() else (f"xurl:{url.lower()}" if url else
                                                 "claim:" + hashlib.sha256(claim.encode()).hexdigest()[:16])
        addrs, txs = split_ids([*x.get("addresses", []), *x.get("transactions", [])])
        overlap = [a for a in addrs if a in known]
        verified += chk.get("verified") is True
        refused = chk.get("verified") is False
        source = {"url": url, "post_id": pid, "author": chk.get("author") or (m.group(1) if m else ""),
                  "created_at": chk.get("created_at") or str(x.get("posted_at", "")), "verified": chk.get("verified"),
                  "time_matches": chk.get("time_matches"), "first_hand": x.get("first_hand"),
                  "text": str(chk.get("text", ""))[:500]}
        lid, added = add_lead(store, key, "x_post", claim or url, state="closed" if refused else "new",
                              owner="none" if refused else "gpt", topic=cell["topic"], period=cell["period"],
                              source_job=job["id"], source_ref=url, sources_json=[source], addresses_json=addrs,
                              txs_json=txs, hypothesis=claim[:1500],
                              checks=(str(x.get("proposed_onchain_check", ""))[:800]
                                      + (f" [overlap with repository addresses: {', '.join(overlap)}]" if overlap else "")
                                      + (" [Grok marks it already in the repository]" if x.get("already_in_repo") else "")),
                              closure_reason=("supervisor re-read: post missing or author differs from its URL"
                                              if refused else ""))
        new += added
        dup += not added
        ids.append(lid)
    outcome = "positive" if new else "negative"
    store.execute("UPDATE searches SET finished=?, posts=?, verified_posts=?, new_leads=?, duplicates=?, outcome=? "
                  "WHERE job_id=?", (now(), len(leads), verified, new, dup, outcome, job["id"]))
    for p in parent:  # an X follow-up of one lead: its new leads are triaged on their own
        update_lead(store, p["id"], state="unresolved", owner="none",
                    closure_reason=f"X follow-up {job['id']}: {len(leads)} post(s), new leads {', '.join(ids) or 'none'}")
    summary = {"posts": len(leads), "verified_posts": verified, "new_leads": new, "duplicates": dup, "leads": ids,
               "x_posts": checks}
    mdir = Path(job["mission_dir"] or cfg.missions_dir / job["id"])
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "campaign_ingest.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    store.set_status(job["id"], "done", f"campaign: {len(leads)} post(s), {verified} re-read, {new} new lead(s), "
                     f"{dup} already registered; triaged by GPT next", expect=("reviewing",), novelty=min(5, new),
                     decision="campaign_ingested")
    store.log("campaign", f"Grok cell ingested: {summary['posts']} posts, {new} new", job_id=job["id"])
    if new:
        store.emit("work.ready", job_id=job["id"])
    return summary


# ---------------------------------------------------------------- GPT triage
def lead_brief(store: Store, lead: dict) -> str:
    addrs = json.loads(lead["addresses_json"])
    others = store.query("SELECT DISTINCT l.id FROM leads l, json_each(l.addresses_json) a WHERE a.value IN "
                         "(SELECT value FROM json_each(?)) AND l.id!=? LIMIT 10", (canonical(addrs), lead["id"]))
    paths = store.query("SELECT DISTINCT source_path FROM known_addresses WHERE lower(address) IN "
                        "(SELECT value FROM json_each(?)) LIMIT 8", (canonical(addrs),))
    return canonical({"lead_id": lead["id"], "kind": lead["kind"], "title": lead["title"], "topic": lead["topic"],
                      "period": lead["period"], "sources": json.loads(lead["sources_json"]), "addresses": addrs,
                      "transactions": json.loads(lead["txs_json"]), "hypothesis": lead["hypothesis"][:800],
                      "checks": lead["checks"][:800], "source_ref": lead["source_ref"],
                      "same_addresses_in_other_leads": [o["id"] for o in others],
                      "addresses_in_repository_files": [p["source_path"] for p in paths]})


def triage(cfg: Config, store: Store, work_id: str) -> dict:
    batch = store.query("SELECT * FROM leads WHERE state='new' ORDER BY priority DESC, created, id LIMIT ?",
                        (cfg.int("CAMPAIGN_TRIAGE_BATCH"),))
    if not batch:
        return {"decided": 0}
    closed = [f"- {r['id']} [{r['state']}] {r['title'][:120]}" for r in store.query(
        "SELECT id, state, title FROM leads WHERE state NOT IN ('new','deferred') ORDER BY updated DESC LIMIT 60")]
    user = (f"LEADS TO TRIAGE (untrusted content from X and earlier agents):\n"
            + "\n".join(lead_brief(store, x) for x in batch)[:30000]
            + f"\n\nLEADS ALREADY HANDLED (do not reopen; a lead about the same case is a duplicate):\n"
            + "\n".join(closed)[:6000]
            + f"\n\nREPOSITORY INVENTORY:\n{inventory.digest(store)[:12000]}\n\n"
            + f"EXISTING NOVELTY KEYS (do not reuse): {canonical(store.recent_keys(150))[:5000]}")
    if not cfg.live:
        out = {"decisions": [{"lead_id": x["id"], "decision": "defer", "duplicate_of": "", "market": "",
                              "event_time_utc": "", "hypothesis": "", "innocent_explanations": [],
                              "scores": {k: 0 for k in schemas.SCORE_KEYS}, "novelty_key": "", "task": "",
                              "falsifier": "", "reason": "dry run"} for x in batch], "gaps": [], "notes": "dry run"}
    else:
        out = providers.openai_json(cfg, store, "triagent_triage", schemas.TRIAGE, TRIAGER, user, work_id)
    return apply_triage(cfg, store, batch, out, work_id)


def apply_triage(cfg: Config, store: Store, batch: list[dict], out: dict, work_id: str) -> dict:
    by_id, counts = {x["id"]: x for x in batch}, {}
    for d in out.get("decisions", []):
        lead = by_id.pop(d["lead_id"], None)
        if not lead:
            store.log("campaign", f"triage decision for an unknown or repeated lead ignored: {d['lead_id'][:40]}",
                      level="warning")
            continue
        decision = d["decision"]
        common = {"score_json": {**d["scores"], "innocent_explanations": d["innocent_explanations"][:6],
                                 "triage": work_id}, "priority": priority(d["scores"]),
                  "market": d["market"][:300] or lead["market"], "hypothesis": d["hypothesis"][:1500] or lead["hypothesis"],
                  "event_ts": parse_utc(d["event_time_utc"]) or lead["event_ts"]}
        if decision in ("investigate", "x_followup"):
            agent = "claude" if decision == "investigate" else "grok"
            if agent == "grok" and store.query("SELECT 1 FROM jobs WHERE id=? AND agent='grok'", (lead["job_id"] or "",)):
                decision = "defer"  # one X follow-up per lead, never a loop
            else:
                inv = lead["investigation"] or f"camp-{lead['id']}"
                store.ensure_investigation(inv, f"Campaign {lead['id']}: {lead['title']}")
                store.execute("UPDATE investigations SET status='open', updated=? WHERE id=?", (now(), inv))
                facts = (f"\n\nLEAD {lead['id']} (registry facts, untrusted): {lead_brief(store, lead)[:2500]}"
                         + (CLAUDE_CHECKLIST if agent == "claude" else ""))
                try:
                    jid = store.enqueue(agent, "analysis" if agent == "claude" else "x_research", d["novelty_key"],
                                        (d["task"][:4500] + facts)[:7900], origin="campaign", investigation=inv,
                                        falsifier=d["falsifier"], priority=common["priority"])
                except ValueError as exc:
                    jid, common["closure_reason"] = None, f"invalid mission: {exc}"
                if jid:
                    update_lead(store, lead["id"], state="investigating", owner=agent, job_id=jid, investigation=inv,
                                closure_reason=d["reason"][:600], **common)
                else:
                    update_lead(store, lead["id"], state="closed", owner="none", investigation=inv,
                                **{"closure_reason": "novelty key already used by an earlier mission: "
                                   + d["reason"][:400], **common})
                counts[decision] = counts.get(decision, 0) + 1
                continue
        if decision == "duplicate":
            update_lead(store, lead["id"], state="duplicate", owner="none",
                        closure_reason=f"duplicate of {d['duplicate_of'][:60]}: {d['reason'][:500]}", **common)
        elif decision == "defer":
            update_lead(store, lead["id"], state="deferred", owner="none", closure_reason=d["reason"][:600], **common)
        else:
            update_lead(store, lead["id"], state="closed", owner="none",
                        closure_reason=f"{decision}: {d['reason'][:600]}", **common)
        counts[decision] = counts.get(decision, 0) + 1
    for lead in by_id.values():  # omitted by GPT: deferred, re-triaged at the next pass, never in a loop
        update_lead(store, lead["id"], state="deferred", closure_reason=f"not decided by triage {work_id}")
        counts["omitted"] = counts.get("omitted", 0) + 1
    gaps = 0
    for g in out.get("gaps", [])[:2]:
        lid, added = add_lead(store, f"gap:{g['novelty_key']}", "gap", g["title"], state="investigating",
                              owner=g["agent"], hypothesis=g["reason"][:1500], score_json=g["scores"],
                              priority=priority(g["scores"]))
        if not added:
            continue
        inv = f"camp-{lid}"
        store.ensure_investigation(inv, f"Campaign gap {lid}: {g['title']}")
        try:
            jid = store.enqueue(g["agent"], "analysis" if g["agent"] == "claude" else "x_research", g["novelty_key"],
                                (g["task"][:5000] + (CLAUDE_CHECKLIST if g["agent"] == "claude" else ""))[:7900],
                                origin="campaign", investigation=inv, falsifier=g["falsifier"],
                                priority=priority(g["scores"]))
        except ValueError:
            jid = None
        update_lead(store, lid, investigation=inv, job_id=jid, **({} if jid else
                    {"state": "closed", "owner": "none", "closure_reason": "novelty key already used"}))
        gaps += bool(jid)
    store.log("campaign", f"triage {work_id}: {canonical(counts)}, {gaps} gap mission(s)")
    return {"decided": sum(counts.values()), "counts": counts, "gaps": gaps}


# ---------------------------------------------------------------- after a reviewed mission
def first_times(store: Store, inv: str) -> tuple[int | None, int | None]:
    rows = {r["text"].split(" ", 1)[0]: r["window_start"] for r in store.query(
        "SELECT text, window_start FROM findings WHERE investigation=? AND type='method' AND text LIKE 'timeline:%' "
        "AND window_start>0 ORDER BY id", (inv,))}
    return rows.get("timeline:first_trade"), rows.get("timeline:event")


def on_review(cfg: Config, store: Store, job: dict) -> str | None:
    """Called after every stored review: settles the lead of a campaign investigation once nothing is pending."""
    leads = store.query("SELECT * FROM leads WHERE investigation=?", (job["investigation"],))
    if not leads:
        return None
    lead, inv = leads[0], job["investigation"]
    if store.query(f"SELECT 1 FROM jobs WHERE investigation=? AND status IN {OPEN_JOB} LIMIT 1", (inv,)):
        update_lead(store, lead["id"])
        return "investigating"
    tiers = [f["tier"] for f in store.query("SELECT tier FROM findings WHERE investigation=? AND type='claim'", (inv,))]
    new_state = ("confirmed" if "CONFIRMED" in tiers else "supported" if "SUPPORTED" in tiers else
                 "refuted" if tiers and all(t == "REFUTED" for t in tiers) else "unresolved")
    novelty = store.query("SELECT max(novelty) n FROM jobs WHERE investigation=?", (inv,))[0]["n"] or 0
    links = store.query("SELECT count(*) n FROM edges e JOIN jobs j ON j.id=e.job_id WHERE j.investigation=? AND "
                        "e.level='receipt_verified'", (inv,))[0]["n"]
    significant = (new_state in ("confirmed", "supported") and novelty >= 3) or links > 0
    first_trade, event = first_times(store, inv)
    update_lead(store, lead["id"], state=new_state, owner="none", first_trade_ts=first_trade or lead["first_trade_ts"],
                event_ts=event or lead["event_ts"],
                closure_reason=f"missions closed: {len(tiers)} claim(s) {canonical(sorted(set(tiers)))}, max novelty "
                               f"{novelty}, {links} receipt-verified link(s); last decision {job.get('decision')}")
    if significant:
        store.execute("UPDATE passes SET significant=significant+1 WHERE n=?", (current_pass(store),))
        store.execute("INSERT INTO publications(investigation,lead,branch,state,created,updated) VALUES "
                      "(?,?,?,'audit_pending',?,?) ON CONFLICT(investigation) DO UPDATE SET state='audit_pending', "
                      "updated=excluded.updated WHERE state NOT IN ('audit_pending','prepared')",
                      (inv, lead["id"], f"triagent/campaign-{lead['id'].lower()}", now(), now()))
        store.emit("work.ready", job_id=inv)
    store.log("campaign", f"lead {lead['id']} -> {new_state}" + (" (significant)" if significant else ""), job_id=job["id"])
    return new_state


# ---------------------------------------------------------------- GPT audit before publication
def dossier(store: Store, inv: str) -> dict:
    jobs = store.query("SELECT id, agent, task, status, novelty, decision, result_json, review_json FROM jobs WHERE "
                       "investigation=? ORDER BY created", (inv,))
    ids = [j["id"] for j in jobs]
    return {"lead": (store.query("SELECT * FROM leads WHERE investigation=?", (inv,)) or [{}])[0], "jobs": jobs,
            "findings": store.query("SELECT type, text, tier, evidence_json, window_start FROM findings WHERE "
                                    "investigation=? ORDER BY id", (inv,)),
            "edges": store.query("SELECT src,dst,kind,chain,tx_hash,token,amount,ts,method,level,evidence_sha256,job_id "
                                 "FROM edges WHERE job_id IN (SELECT value FROM json_each(?)) ORDER BY ts", (canonical(ids),)),
            "evidence": store.query("SELECT sha256, source, ref, chain, fetched_at, bytes, path, job_id FROM evidence "
                                    "WHERE job_id IN (SELECT value FROM json_each(?))", (canonical(ids),))}


def audit(cfg: Config, store: Store, inv: str, work_id: str) -> str:
    d = dossier(store, inv)
    missions = []
    for j in d["jobs"]:
        rep = (json.loads(j["result_json"]) if j["result_json"] else {}).get("report", {})
        rev = json.loads(j["review_json"]) if j["review_json"] else {}
        missions.append({"job": j["id"], "agent": j["agent"], "task": j["task"][:1500], "summary": str(rep.get("summary", ""))[:2500],
                         "review": {k: rev.get(k) for k in ("analysis", "claims", "novelty", "decision", "risks")},
                         "evidence_check": (rev.get("checks") or {}).get("evidence")})
    user = (f"LEAD: {lead_brief(store, d['lead'])}\n\nMISSIONS AND REVIEWS:\n{canonical(missions)[:30000]}\n\n"
            f"FINDINGS:\n{canonical(d['findings'])[:12000]}\n\nEDGES (level is the supervisor's check):\n"
            f"{canonical(d['edges'][:150])[:12000]}\n\nEVIDENCE INDEX (sha256, source, ref):\n"
            + "\n".join(f"{e['sha256']} {e['source']} {e['ref'][:160]}" for e in d["evidence"])[:15000]
            + f"\n\nREPOSITORY INVENTORY:\n{inventory.digest(store)[:8000]}")
    out = providers.openai_json(cfg, store, "triagent_audit", schemas.AUDIT, AUDITOR, user, work_id) if cfg.live else \
        {"publishable": False, "reason": "dry run", "title": "", "summary": "", "claims": [], "timeline": [],
         "first_trade_time_utc": "", "event_time_utc": "", "innocent_explanations": [], "limits": [], "not_demonstrated": []}
    return apply_audit(store, inv, out, d)


def apply_audit(store: Store, inv: str, out: dict, d: dict | None = None) -> str:
    """GPT proposes; a claim is published only if each of its evidence ids is archived by this investigation."""
    d = d or dossier(store, inv)
    known = {e["sha256"] for e in d["evidence"]}
    kept, dropped = [], []
    for c in out.get("claims", []):
        ok = c["tier"] in ("CONFIRMED", "SUPPORTED") and c["evidence_ids"] and all(
            e in known or e.startswith("repo:") for e in c["evidence_ids"])
        (kept if ok else dropped).append(c)
    publish = bool(out.get("publishable")) and bool(kept)
    reason = out.get("reason", "")[:800] if publish else ("no SUPPORTED or CONFIRMED claim whose evidence is archived"
                                                          if out.get("publishable") else out.get("reason", "")[:800])
    store.execute("UPDATE publications SET state=?, audit_json=?, reason=?, updated=? WHERE investigation=?",
                  ("prepared" if publish else "refused", canonical({**out, "kept_claims": kept, "dropped_claims": dropped}),
                   reason, now(), inv))
    lead = d["lead"]
    if lead:
        update_lead(store, lead["id"], first_trade_ts=parse_utc(out.get("first_trade_time_utc")) or lead.get("first_trade_ts"),
                    event_ts=parse_utc(out.get("event_time_utc")) or lead.get("event_ts"))
    store.log("campaign", f"audit {inv}: {'prepared for publication' if publish else 'refused'} "
                          f"({len(kept)} claim(s) kept, {len(dropped)} dropped)")
    return "prepared" if publish else "refused"


# ---------------------------------------------------------------- passes, saturation, maintenance
def pass_idle(store: Store, n: int) -> bool:
    return not (next_cell(store, n)
                or store.query("SELECT 1 FROM searches WHERE pass=? AND finished IS NULL LIMIT 1", (n,))
                or store.query("SELECT 1 FROM leads WHERE state IN ('new','investigating') LIMIT 1")
                or store.query(f"SELECT 1 FROM jobs WHERE origin='campaign' AND status IN {OPEN_JOB} LIMIT 1")
                or store.query("SELECT 1 FROM publications WHERE state IN ('audit_pending','prepared') LIMIT 1"))


def close_pass(cfg: Config, store: Store, n: int, notifier) -> str:
    row = store.query("SELECT count(*) s, coalesce(sum(new_leads),0) l FROM searches WHERE pass=?", (n,))[0]
    sig = store.query("SELECT significant FROM passes WHERE n=?", (n,))
    sig = sig[0]["significant"] if sig else 0
    store.execute("INSERT OR IGNORE INTO passes(n, started) VALUES (?, ?)", (n, now()))
    store.execute("UPDATE passes SET ended=?, searches=?, new_leads=?, summary=? WHERE n=?",
                  (now(), row["s"], row["l"], f"{row['s']} searches, {row['l']} new leads, {sig} significant", n))
    prev = store.query("SELECT significant FROM passes WHERE n=?", (n - 1,))
    if n >= 2 and sig == 0 and prev and prev[0]["significant"] == 0:
        return saturate(cfg, store, notifier)
    store.execute("INSERT OR IGNORE INTO passes(n, started) VALUES (?, ?)", (n + 1, now()))
    store.set_kv("campaign.pass", n + 1)
    store.execute("UPDATE leads SET state='new', updated=? WHERE state='deferred'", (now(),))  # one more look per pass
    store.log("campaign", f"pass {n} closed ({sig} significant); pass {n + 1} starts")
    store.emit("work.ready", job_id="campaign")
    return f"pass {n + 1}"


def saturate(cfg: Config, store: Store, notifier) -> str:
    store.set_kv("campaign.state", "saturated")
    store.set_kv("campaign.saturated_at", now())
    path = cfg.state_dir / "campaign" / "COVERAGE_REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(coverage_report(store))
    store.log("campaign", f"campaign saturated after two passes without a significant result; report {path}")
    notify_saturation(cfg, store, notifier)
    return "saturated"


def notify_saturation(cfg: Config, store: Store, notifier) -> None:
    from . import reports  # reports imports nothing from here; local import keeps module load order simple
    if store.get_kv("campaign.saturation_notified") == "1" or state(store) != "saturated":
        return
    sent = reports.notify(store, cfg, "campaign", f"saturation:{current_pass(store)}:{now() // 86400}", "TriAgent",
                          "Campagne historique arrivée à saturation — bilan disponible", "campaign", notifier)
    if sent:
        store.set_kv("campaign.saturation_notified", "1")


def tick(cfg: Config, sup, notifier) -> dict:
    """From the maintenance step (no model call): ingest finished Grok cells, keep one cell queued, close passes."""
    store = sup.store
    if state(store) == "saturated":
        notify_saturation(cfg, store, notifier)  # retried daily if the quota refused it
        return {}
    if state(store) != "running" or now() - int(store.get_kv("campaign.tick") or 0) < 20:
        return {}
    store.set_kv("campaign.tick", now())
    out = {"ingested": 0}
    for job in store.jobs("agent='grok' AND origin='campaign' AND status='reviewing'", limit=5):
        try:
            ingest_grok(cfg, store, job)
            out["ingested"] += 1
        except Exception as exc:  # stored result kept; never re-run Grok for it
            store.set_status(job["id"], "blocked", f"campaign ingestion failed: {exc}"[:500], expect=("reviewing",))
            store.execute("UPDATE searches SET finished=?, outcome='failed' WHERE job_id=?", (now(), job["id"]))
    n = current_pass(store)
    for s in store.query("SELECT s.job_id FROM searches s JOIN jobs j ON j.id=s.job_id WHERE s.finished IS NULL AND "
                         "j.status IN ('failed','blocked')"):  # a failed cell counts as examined-with-failure
        store.execute("UPDATE searches SET finished=?, outcome='failed' WHERE job_id=?", (now(), s["job_id"]))
    for lead in store.query(f"SELECT l.id, l.job_id FROM leads l WHERE l.state='investigating' AND NOT EXISTS (SELECT 1 "
                            f"FROM jobs j WHERE j.investigation=l.investigation AND j.status IN {OPEN_JOB})"):
        j = store.job(lead["job_id"] or "") or {}
        if j.get("status") == "done":  # its follow-ups ended without a review: settle from what was reviewed
            on_review(cfg, store, j)
        else:  # failed or blocked without a review: settled, kept visible
            update_lead(store, lead["id"], state="unresolved", owner="none",
                        closure_reason=f"mission {lead['job_id']} ended {j.get('status')} without a review: "
                                       f"{str(j.get('status_reason'))[:300]}")
    open_grok = store.query(f"SELECT 1 FROM jobs WHERE agent='grok' AND origin='campaign' AND status IN {OPEN_JOB} LIMIT 1")
    cell = next_cell(store, n)
    if cell and not open_grok and not sup.gate() and not sup.held("xai") and not providers.unavailable(cfg, "grok") \
            and grok_capacity(cfg, store):
        out["queued_cell"] = cell if enqueue_cell(store, n, cell) else None
    if not cell and pass_idle(store, n):
        out["pass"] = close_pass(cfg, store, n, notifier)
    from . import reports
    for p in store.query("SELECT investigation, state, reason, attempts FROM publications WHERE state='tests_failed' OR "
                         "(state='push_failed' AND attempts>=3)"):  # a persistent problem or an owner decision
        reports.notify(store, cfg, "blocked", f"publish:{p['investigation']}:{p['state']}:{p['attempts']}",
                       "TriAgent : publication bloquée", f"{p['investigation']} : {p['reason'][:200]}", "campaign", notifier)
    return out


def grok_capacity(cfg: Config, store: Store) -> bool:
    """grok_cli runs on the grok.com plan: its dollar figure is the CLI's estimate, not a bill, so only the daily
    call cap applies (as for Codex on the ChatGPT plan). Other modes keep the dollar budget too."""
    if cfg.get("GROK_MODE") == "grok_cli":
        return store.spent("xai", providers.day_start())[1] < cfg.int("GROK_MAX_MISSIONS_DAY")
    return providers.budget_ok(store, cfg, "xai")[0]


def next_gpt_work(store: Store) -> tuple[str, str] | None:
    """(task_type, work_id) of campaign GPT work, for the broker: a triage batch first, then a publication audit."""
    if state(store) not in ("running", "saturated"):
        return None
    if store.query("SELECT 1 FROM leads WHERE state='new' LIMIT 1") and \
            now() >= int(store.get_kv("campaign.triage_after") or 0):
        return "triage", f"campaign-triage-{now() // 60}"
    row = store.query("SELECT investigation FROM publications WHERE state='audit_pending' ORDER BY updated LIMIT 1")
    if row and now() >= int(store.get_kv("campaign.audit_after") or 0):
        return "audit", f"campaign-audit-{row[0]['investigation']}"
    return None


def run_gpt(sup, task_type: str, work_id: str) -> None:
    """One GPT session for a triage batch or an audit; errors hold the provider or delay the task, never loop."""
    cfg, store = sup.cfg, sup.store
    gpt = "codex_cli" if cfg.get("OPENAI_MODE") == "codex_cli" else "openai_api"
    store.run_start(gpt, task_type, work_id, mode=sup.mode_label("gpt"))
    try:
        if task_type == "triage":
            triage(cfg, store, work_id)
        else:
            audit(cfg, store, work_id.removeprefix("campaign-audit-"), work_id)
        store.run_end(work_id, "ok", gpt)
    except ProviderError as exc:
        store.run_end(work_id, exc.kind, gpt)
        sup.on_provider_error("openai", exc)
        if exc.kind in ("uncertain", "permanent"):  # a failed batch waits an hour instead of being resent at once
            store.set_kv(f"campaign.{task_type}_after", now() + 3600)
            store.log("campaign", f"{task_type} {work_id} failed ({exc.kind}); retried in 1 h", level="warning")


# ---------------------------------------------------------------- views and reports (no model call)
def coverage(store: Store) -> list[dict]:
    return store.query("SELECT topic, period, count(*) searches, max(pass) last_pass, coalesce(sum(posts),0) posts, "
                       "coalesce(sum(verified_posts),0) verified, coalesce(sum(new_leads),0) new_leads, "
                       "sum(outcome='negative') negative, sum(outcome='failed') failed FROM searches GROUP BY topic, period")


def detector_rows(store: Store) -> list[dict]:
    """Phase of every dated link of a campaign case: A before the first bet, B between entry and event, C after.
    Phases come from timestamps only; C is never evidence of what was visible in A."""
    out = []
    for lead in store.query("SELECT id, state, investigation, first_trade_ts, event_ts FROM leads WHERE "
                            "investigation LIKE 'camp-%' AND first_trade_ts IS NOT NULL"):
        for e in store.query("SELECT e.src, e.dst, e.kind, e.level, e.chain, e.tx_hash, e.amount, e.ts FROM edges e JOIN "
                             "jobs j ON j.id=e.job_id WHERE j.investigation=? AND e.ts IS NOT NULL", (lead["investigation"],)):
            phase = "A" if e["ts"] < lead["first_trade_ts"] else ("B" if not lead["event_ts"] or e["ts"] < lead["event_ts"] else "C")
            out.append({"lead": lead["id"], "lead_state": lead["state"], "phase": phase,
                        "first_trade_ts": lead["first_trade_ts"], "event_ts": lead["event_ts"], **e})
    return out


def summary(store: Store) -> dict:
    n = current_pass(store)
    by_state = {r["state"]: r["n"] for r in store.query("SELECT state, count(*) n FROM leads GROUP BY state")}
    passes = store.query("SELECT * FROM passes ORDER BY n")
    searched = store.query("SELECT count(DISTINCT cell) n FROM searches WHERE pass=?", (n,))[0]["n"]
    searches = store.query("SELECT count(*) n FROM searches")[0]["n"]
    significant = sum(p["significant"] for p in passes)
    return {"state": state(store), "pass": n, "cells_total": len(TOPICS) * len(PERIODS), "cells_searched_this_pass": searched,
            "leads": by_state, "leads_total": sum(by_state.values()), "passes": passes,
            "yield": {"searches": searches, "significant": significant,
                      "significant_per_10_searches": round(10 * significant / searches, 2) if searches else None},
            "saturated_at": store.get_kv("campaign.saturated_at")}


def coverage_report(store: Store) -> str:
    s = summary(store)
    lines = [f"# Historical campaign: coverage report ({time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())})", "",
             f"State: {s['state']}, pass {s['pass']}. Saturation means the defined sources and leads were examined "
             "without a new sufficiently relevant result; it does not mean every case of insider trading was found.", "",
             "## Passes", "", "| Pass | Started | Ended | Searches | New leads | Significant |", "|---|---|---|---|---|---|"]
    live = {r["pass"]: r for r in store.query("SELECT pass, count(*) s, coalesce(sum(new_leads),0) l FROM searches "
                                              "GROUP BY pass")}  # an open pass has no closing totals yet
    lines += [f"| {p['n']} | {iso(p['started'])} | {iso(p['ended'])} | {live.get(p['n'], {}).get('s', 0)} | "
              f"{live.get(p['n'], {}).get('l', 0)} | {p['significant']} |" for p in s["passes"]]
    lines += ["", "## Coverage (topic x period)", "", "| Topic | Period | Searches | Posts | Re-read | New leads | Negative | Failed |",
              "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {c['topic']} | {c['period']} | {c['searches']} | {c['posts']} | {c['verified']} | {c['new_leads']} | "
              f"{c['negative']} | {c['failed']} |" for c in coverage(store)]
    lines += ["", "## Leads by state", ""] + [f"- {k}: {v}" for k, v in sorted(s["leads"].items())]
    lines += ["", "## Unresolved and deferred leads", ""]
    lines += [f"- {r['id']} [{r['state']}] {r['title'][:160]}: {r['closure_reason'][:200]}" for r in store.query(
        "SELECT id, state, title, closure_reason FROM leads WHERE state IN ('unresolved','deferred') ORDER BY priority DESC LIMIT 200")]
    phases = {}
    for r in detector_rows(store):
        phases[r["phase"]] = phases.get(r["phase"], 0) + 1
    lines += ["", "## For the prospective detector", "",
              f"Dated links by phase (A before the first bet, B before the event, C after): {canonical(phases)}. "
              "No model is calibrated or enabled from these cases; labels are lead states, not proof of insider "
              "trading. Next: out-of-sample chronological validation, placebo dates and false positives per 1,000 "
              "accounts with `triagent backtest` once enough dated cases exist.", "",
              "## Limits", "",
              "- Grok CLI searches the web, not the X API: coverage of X is unknown and deleted posts are invisible.",
              "- Post re-reads use X's public embed endpoint, which is undocumented; a failed re-read is 'not verified'.",
              "- Subscription quotas bound the pace (Grok, Claude and Codex daily caps); a cell is one search per pass.",
              "- Wallet or exchange addresses never establish identity or common ownership."]
    return "\n".join(lines) + "\n"


def iso(ts) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(int(ts))) if ts else "—"


# ---------------------------------------------------------------- export to the repository (no model call)
LEAD_COLS = ("id", "dedup_key", "kind", "topic", "period", "state", "priority", "owner", "market", "title", "hypothesis",
             "checks", "closure_reason", "investigation", "job_id", "source_job", "source_ref", "pass")
POST_COLS = ("post_url", "post_author", "post_time_utc", "post_reread", "post_text")


def export(store: Store, out: Path) -> dict:
    """The registry as files for a research note: leads, known cases, searches, a report, an offline verifier."""
    from .publish import csv_text, utc  # publish imports campaign at load time; this import stays local
    out.mkdir(parents=True, exist_ok=True)
    leads = store.query("SELECT * FROM leads ORDER BY id")
    known = [x for x in leads if x["dedup_key"].startswith("case:inv:")]
    rows = []
    for x in leads:
        if x["dedup_key"].startswith("case:inv:"):
            continue
        src = (json.loads(x["sources_json"]) or [{}])[0]
        rows.append({**{k: x[k] for k in LEAD_COLS}, "addresses": " ".join(json.loads(x["addresses_json"])),
                     "transactions": " ".join(json.loads(x["txs_json"])), "scores": x["score_json"],
                     "created_utc": utc(x["created"]), "updated_utc": utc(x["updated"]), "post_url": src.get("url", ""),
                     "post_author": src.get("author", ""), "post_time_utc": src.get("created_at", ""),
                     "post_reread": {True: "yes", False: "no"}.get(src.get("verified"), "not checked"),
                     "post_text": " ".join(str(src.get("text", "")).split())})
    files = {
        "LEADS.csv": csv_text([*LEAD_COLS, "addresses", "transactions", "scores", *POST_COLS, "created_utc",
                               "updated_utc"], rows),
        "KNOWN_CASES.csv": csv_text(["id", "dedup_key", "title", "source_ref", "closure_reason"], known),
        "SEARCHES.csv": csv_text(["job_id", "cell", "topic", "period", "pass", "created_utc", "finished_utc", "posts",
                                  "verified_posts", "new_leads", "duplicates", "outcome"],
                                 [{**r, "created_utc": utc(r["created"]), "finished_utc": utc(r["finished"])}
                                  for r in store.query("SELECT * FROM searches ORDER BY id")]),
        "REPORT.md": export_report(store, rows),
    }
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    (out / "verify.py").write_bytes(Path(__file__).with_name("registry_verify.py").read_bytes())
    return {"leads": len(rows), "known_cases": len(known), "files": sorted([*files, "verify.py"])}


def export_report(store: Store, rows: list[dict]) -> str:
    by_state: dict[str, int] = {}
    for r in rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1
    open_rows = [r for r in rows if r["state"] == "investigating"]
    lines = ["# TriAgent historical campaign: registry of examined leads", "",
             f"State of the campaign's SQLite registry, exported {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} "
             f"(campaign state: {state(store)}). Every row is a lead: a public claim to check, never a finding. Nothing "
             "here establishes insider trading, identity or common ownership; no financial claim is published here.", "",
             "## Files", "",
             "- [LEADS.csv](LEADS.csv): every lead from X and from the repository's intake notes, with its dedup key, "
             "state, GPT scores, closure reason and the X post as re-read by the supervisor (author and UTC time from "
             "X's public embed endpoint).",
             "- [KNOWN_CASES.csv](KNOWN_CASES.csv): the repository investigations registered as closed known cases, so that a "
             "duplicate decision can point to them.",
             "- [SEARCHES.csv](SEARCHES.csv): every Grok search cell (topic x period), positive, negative or failed.",
             "- `verify.py`: offline consistency checks of these three files (no network).", "",
             "## Leads by state", "", "| State | Leads |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(by_state.items())]
    lines += ["", "## Open leads (missions designed, not run)", ""]
    lines += [f"- `{r['id']}` ({r['owner']}, mission `{r['job_id']}`): {r['title'][:220]}" for r in open_rows] or ["- none"]
    body = coverage_report(store).split("\n", 2)[2]  # the coverage report without its title line
    return "\n".join(lines) + "\n\n" + body
