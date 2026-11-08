"""Draft PRs for audited campaign dossiers. No model call.

One isolated branch per investigation (`triagent/campaign-<lead>`), built on a fresh `origin/main` (or the existing
branch with `origin/main` merged in), one directory `research_notes/triagent-campaign/<lead>/` written from SQLite
and the archived evidence, then every check of the repository's AGENTS.md and CI plus the note's own `verify.py`.
Only when all pass: a normal push (never force, never main, never the README) and `gh pr create --draft`, or an
update of the same PR. A failing check stops the publication and keeps its output; nothing is skipped to get green.
Raw API pages (which carry account names and bios) are never copied: only their URL and SHA-256 are listed; chain
receipts used by verified flows are archived with the note so `verify.py` re-checks them offline.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import campaign
from .config import Config
from .store import Store, canonical, now, sha256_bytes
from .util import SECRET_PATTERNS

NOTE_ROOT = "research_notes/triagent-campaign"
BRANCH_PREFIX = "triagent/campaign-"  # the only refs this module ever pushes
CHECKS = (("check_publication", ["scripts/check_publication.py", "--target", "main", "--candidate", "HEAD",
                                 "--base-ref", "origin/main"]),
          ("test_publication", ["scripts/test_publication.py"]),
          ("test_phi", ["scripts/test_phi.py"]),
          ("test_integrity_regressions", ["scripts/test_integrity_regressions.py"]),
          ("test_parallel_publication", ["scripts/test_parallel_publication.py"]),
          ("validate_evidence", ["scripts/validate_evidence.py"]),
          ("build_master_report", ["scripts/build_master_report.py", "--check"]),
          ("relay_verify", ["research_notes/relay-followup-2026-11-04/verify.py"]),
          ("research_links", ["scripts/check_research_links.py"]))
ACTIVITY_KEEP = ("proxy_wallet", "timestamp", "condition_id", "type", "side", "outcome", "size", "usdc_size", "price",
                 "transaction_hash", "title")  # never name, pseudonym, bio or profile image
LOCK = threading.Lock()
MAX_EVIDENCE_BYTES = 2_000_000


class PublishError(Exception):
    pass


def run(cmd: list[str], cwd: Path, timeout: int = 600, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_TERMINAL_PROMPT": "0", **(env or {})})


def git(repo: Path, *args: str, check: bool = True, timeout: int = 300) -> str:
    p = run(["git", *args], repo, timeout)
    if check and p.returncode:
        raise PublishError(f"git {args[0]} failed: {(p.stderr or p.stdout)[-400:]}")
    return p.stdout.strip()


def gh_bin(cfg: Config) -> str:
    return cfg.get("GH_BIN") or shutil.which("gh") or str(Path.home() / ".local/bin/gh")


def ensure_clone(cfg: Config) -> Path:
    repo = cfg.state_dir / "publish-repo"
    if not (repo / ".git").exists():
        url = cfg.get("PUBLISH_REMOTE") or git(cfg.repo_dir, "remote", "get-url", "origin")
        p = run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", url, str(repo)], cfg.state_dir, 900)
        if p.returncode:
            raise PublishError(f"clone failed: {p.stderr[-300:]}")
        git(repo, "config", "user.name", "TriAgent campaign")
        git(repo, "config", "user.email", "triagent@localhost.invalid")
    return repo


# ---------------------------------------------------------------- note contents
def csv_text(header: list[str], rows: list[dict]) -> str:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=header, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: "" if r.get(k) is None else r.get(k) for k in header})
    return out.getvalue()


def utc(ts) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(ts))) if ts else ""


def activity_rows(evidence: list[dict], addresses: set[str]) -> list[dict]:
    """Rows of archived Polymarket activity pages for the lead's accounts, without any profile field."""
    seen, out = set(), []
    for e in evidence:
        if "data-api.polymarket.com/v2/activity" not in e["ref"] or not Path(e["path"]).is_file():
            continue
        try:
            data = json.loads(Path(e["path"]).read_bytes())
        except (ValueError, OSError):
            continue
        for r in (data.get("data") if isinstance(data, dict) else data) or []:
            if not isinstance(r, dict) or str(r.get("proxy_wallet", "")).lower() not in addresses:
                continue
            key = (r.get("transaction_hash"), r.get("type"), r.get("condition_id"), r.get("size"), r.get("side"))
            if key not in seen:
                seen.add(key)
                out.append({k: r.get(k) for k in ACTIVITY_KEEP} | {"source_sha256": e["sha256"]})
    return sorted(out, key=lambda r: (str(r["proxy_wallet"]), r.get("timestamp") or 0))


def reconcile(rows: list[dict], market: str) -> list[dict]:
    acc: dict[str, dict] = {}
    for r in rows:
        a = acc.setdefault(r["proxy_wallet"], {"address": r["proxy_wallet"], "deposits": 0.0, "withdrawals": 0.0,
                                               "buys": 0.0, "sells": 0.0, "redeems": 0.0, "market_buys": 0.0,
                                               "market_sells": 0.0, "market_redeems": 0.0, "rows": 0})
        usd, t = float(r.get("usdc_size") or 0), r.get("type")
        in_market = bool(market) and r.get("condition_id") == market
        a["rows"] += 1
        if t == "DEPOSIT":
            a["deposits"] += usd
        elif t == "WITHDRAWAL":
            a["withdrawals"] += usd
        elif t == "TRADE":
            side = "buys" if r.get("side") == "BUY" else "sells"
            a[side] += usd
            if in_market:
                a["market_" + side] += usd
        elif t == "REDEEM":
            a["redeems"] += usd
            if in_market:
                a["market_redeems"] += usd
    for a in acc.values():
        a["net_trading"] = round(a["sells"] + a["redeems"] - a["buys"], 2)
        a["net_market"] = round(a["market_sells"] + a["market_redeems"] - a["market_buys"], 2)
        for k in list(a):
            if isinstance(a[k], float):
                a[k] = round(a[k], 2)
    return list(acc.values())


def mermaid(edges: list[dict]) -> str:
    nodes, lines = {}, ["```mermaid", "graph LR"]
    for e in edges[:60]:
        for a in (e["src"], e["dst"]):
            nodes.setdefault(a, f"n{len(nodes)}")
        label = f"{e['kind']} {e['amount'] or ''} {e['chain']}".strip().replace('"', "'")
        arrow = "-->" if e["level"] == "receipt_verified" else "-.->"
        lines.append(f'  {nodes[e["src"]]}["{e["src"][:10]}…"] {arrow}|"{label}"| {nodes[e["dst"]]}["{e["dst"][:10]}…"]')
    return "\n".join(lines + ["```"]) if len(lines) > 2 else "_No dated financial link recorded._"


def table(rows: list[list[str]]) -> list[str]:
    clean = [[" ".join(str(c).replace("|", "/").split()) for c in r] for r in rows]
    return ["| " + " | ".join(clean[0]) + " |", "|" + "---|" * len(clean[0])] + ["| " + " | ".join(r) + " |" for r in clean[1:]]


def build_note(cfg: Config, store: Store, inv: str) -> dict[str, bytes]:
    pub = store.query("SELECT * FROM publications WHERE investigation=?", (inv,))[0]
    audit = json.loads(pub["audit_json"])
    d = campaign.dossier(store, inv)
    lead = d["lead"]
    first, event = lead.get("first_trade_ts"), lead.get("event_ts")
    addrs = {a.lower() for a in json.loads(lead.get("addresses_json") or "[]")}
    addrs |= {e["src"] for e in d["edges"]} | {e["dst"] for e in d["edges"]}
    cited = {ev for c in audit["kept_claims"] for ev in c["evidence_ids"]}
    needed = cited | {e["evidence_sha256"] for e in d["edges"] if e["level"] == "receipt_verified" and e["evidence_sha256"]}
    files: dict[str, bytes] = {}
    sources = []
    for e in d["evidence"]:
        path, include = Path(e["path"]), False
        receipt = "getTransactionReceipt" in e["ref"] or "getTransaction" in e["ref"]
        if e["sha256"] in needed and receipt and path.is_file() and path.stat().st_size <= MAX_EVIDENCE_BYTES:
            raw = path.read_bytes()
            if sha256_bytes(raw) == e["sha256"]:
                files[f"evidence/{e['sha256']}.json"] = raw
                include = True
        sources.append({"sha256": e["sha256"], "kind": e["source"], "ref": e["ref"], "chain": e["chain"] or "",
                        "fetched_utc": utc(e["fetched_at"]), "bytes": e["bytes"], "cited": "yes" if e["sha256"] in cited else "",
                        "included": "yes" if include else "no", "path": f"evidence/{e['sha256']}.json" if include else ""})
    x_sources = json.loads(lead.get("sources_json") or "[]")
    act = activity_rows(d["evidence"], addrs)
    timeline = [{"time_utc": t["time_utc"], "unix": campaign.parse_utc(t["time_utc"]) or "",
                 "event": t["event"], "evidence_ids": " ".join(t["evidence_ids"])} for t in audit["timeline"]]
    timeline += [{"time_utc": utc(e["ts"]), "unix": e["ts"], "event": f"{e['kind']} {e['src']} -> {e['dst']} {e['amount']} "
                  f"{e['token']} ({e['level']}, tx {e['tx_hash']})", "evidence_ids": e["evidence_sha256"] or ""}
                 for e in d["edges"] if e["ts"]]
    for t in timeline:
        t["phase"] = campaign_phase(t["unix"] or None, first, event)
    timeline.sort(key=lambda t: (t["unix"] == "", t["unix"] or 0))
    labels = {r["address"]: r["tags_json"] for r in store.query("SELECT address, tags_json FROM labels WHERE address IN "
                                                                "(SELECT value FROM json_each(?))", (canonical(sorted(addrs)),))}
    lead_addrs = set(json.loads(lead.get("addresses_json") or "[]"))
    addresses = [{"address": a, "in_lead": "yes" if a in lead_addrs else "",
                  "as_source": sum(e["src"] == a for e in d["edges"]), "as_destination": sum(e["dst"] == a for e in d["edges"]),
                  "service_tags": labels.get(a, "")} for a in sorted(addrs)]
    claims = [{"n": i + 1, "statement": c["statement"], "tier": c["tier"], "evidence_ids": " ".join(c["evidence_ids"]),
               "verification_method": c["verification_method"]} for i, c in enumerate(audit["kept_claims"])]
    meta = {"lead": lead["id"], "investigation": inv, "first_trade_ts": first, "event_ts": event,
            "jobs": [j["id"] for j in d["jobs"]], "audit_sha256": sha256_bytes(pub["audit_json"].encode())}
    files["CLAIMS.csv"] = csv_text(["n", "statement", "tier", "evidence_ids", "verification_method"], claims).encode()
    files["TIMELINE.csv"] = csv_text(["time_utc", "unix", "phase", "event", "evidence_ids"], timeline).encode()
    files["ADDRESSES.csv"] = csv_text(["address", "in_lead", "as_source", "as_destination", "service_tags"], addresses).encode()
    files["FLOWS.csv"] = csv_text(["src", "dst", "kind", "level", "chain", "tx_hash", "token", "amount", "ts", "method",
                                   "evidence_sha256", "job_id"], d["edges"]).encode()
    files["POSITIONS.csv"] = csv_text([*ACTIVITY_KEEP, "source_sha256"], act).encode()
    files["RECONCILIATION.csv"] = csv_text(["address", "rows", "deposits", "withdrawals", "buys", "sells", "redeems",
                                            "net_trading", "market_buys", "market_sells", "market_redeems", "net_market"],
                                           reconcile(act, lead.get("market") or "")).encode()
    files["SOURCES.csv"] = csv_text(["sha256", "kind", "ref", "chain", "fetched_utc", "bytes", "cited", "included", "path"],
                                    sources).encode()
    files["DETECTOR_SIGNALS.csv"] = csv_text(["phase", "kind", "level", "src", "dst", "chain", "tx_hash", "amount", "ts"],
                                             [{**e, "phase": campaign_phase(e["ts"], first, event)} for e in d["edges"] if e["ts"]]).encode()
    files["meta.json"] = (json.dumps(meta, indent=1) + "\n").encode()
    files["verify.py"] = (Path(__file__).with_name("note_verify.py")).read_bytes()
    files["REPORT.md"] = report_md(lead, audit, d, x_sources, timeline, claims, meta).encode()
    return files


def campaign_phase(ts, first, event) -> str:
    if not first or ts in (None, ""):
        return ""
    return "A" if int(ts) < first else ("B" if not event or int(ts) < event else "C")


def report_md(lead, audit, d, x_sources, timeline, claims, meta) -> str:
    lines = [f"# {audit['title'] or lead['title']}", "",
             f"TriAgent historical campaign, lead `{lead['id']}`. Draft generated from the programme's memory and audited "
             "by GPT; not yet reviewed by the repository owner. Selection signals and X posts are leads, never proof of "
             "insider trading; an exchange address is not an identity.", "", "## Summary", "", audit["summary"], "",
             "## Published facts", ""]
    lines += table([["#", "Statement", "Tier", "Evidence (SHA-256)", "How to re-check"]] +
                   [[c["n"], c["statement"], c["tier"], c["evidence_ids"][:200], c["verification_method"]] for c in claims])
    lines += ["", "## Timeline (UTC)", "",
              f"First bet: {utc(meta['first_trade_ts']) or 'unknown'}; event: {utc(meta['event_ts']) or 'unknown'}. Phase A is "
              "before the first bet, B between entry and event, C after; C is never evidence of what was visible in A.", ""]
    lines += table([["Time", "Phase", "Event"]] + [[t["time_utc"], t["phase"] or "—", t["event"][:300]] for t in timeline[:80]])
    lines += ["", "## Financial flows", "", "Solid arrows: a Transfer log found in the archived receipt; dotted: reported "
              "or derived only. Full list: [FLOWS.csv](FLOWS.csv), addresses: [ADDRESSES.csv](ADDRESSES.csv).", "",
              mermaid(d["edges"]), "", "## Positions and reconciliation", "",
              "From the archived Polymarket activity pages only (see [POSITIONS.csv](POSITIONS.csv) and "
              "[RECONCILIATION.csv](RECONCILIATION.csv)); a page set that did not reach the end of the history makes "
              "these sums lower bounds.", "", "## Sources", ""]
    lines += [f"- X: {s.get('url')} by @{s.get('author') or '?'} at {s.get('created_at') or '?'} "
              f"(re-read by the supervisor: {s.get('verified')})" for s in x_sources]
    lines += ["- On-chain and API sources with SHA-256: [SOURCES.csv](SOURCES.csv); receipts used by verified flows are in "
              "`evidence/`.", "", "## Innocent explanations", ""] + [f"- {x}" for x in audit["innocent_explanations"]]
    lines += ["", "## Not demonstrated", ""] + [f"- {x}" for x in audit["not_demonstrated"]]
    lines += ["", "## Limits", ""] + [f"- {x}" for x in audit["limits"]]
    lines += ["", "## Method and reproduction", "",
              f"Missions (fresh sessions, read-only tools): {', '.join(meta['jobs'])}. Each Claude Code mission archives every "
              "response it fetched under its SHA-256; the supervisor replays reported Polygon transfers against their "
              "receipt before marking them verified; Codex reviewed each mission and audited this dossier.",
              "", "Offline re-check: `python3 verify.py` (no network).", ""]
    return "\n".join(lines)


def secret_hits(cfg: Config, files: dict[str, bytes]) -> list[str]:
    hits = []
    secrets = [v for v in cfg.secrets.values() if v and len(v) >= 8]
    for name, raw in files.items():
        text = raw.decode("utf-8", "replace")
        if any(s in text for s in secrets) or any(p.search(text) for p in SECRET_PATTERNS):
            hits.append(name)
    return hits


# ---------------------------------------------------------------- one publication
def set_pub(store: Store, inv: str, **fields):
    fields["updated"] = now()
    store.execute(f"UPDATE publications SET {','.join(f'{k}=?' for k in fields)} WHERE investigation=?",
                  [*fields.values(), inv])


def publish(cfg: Config, store: Store, inv: str) -> str:
    pub = store.query("SELECT * FROM publications WHERE investigation=?", (inv,))[0]
    lead_id = pub["lead"]
    branch = pub["branch"]
    if not branch.startswith(BRANCH_PREFIX) or not re.fullmatch(r"[a-z0-9/._-]+", branch) or ".." in branch:
        set_pub(store, inv, state="refused", reason=f"branch {branch!r} is not a campaign research branch")
        return "refused"
    set_pub(store, inv, attempts=pub["attempts"] + 1)
    try:
        repo = ensure_clone(cfg)
        git(repo, "fetch", "-q", "origin", "main", timeout=600)
        exists = run(["git", "fetch", "-q", "origin", f"{branch}:refs/remotes/origin/{branch}"], repo, 600).returncode == 0
        git(repo, "checkout", "-q", "-f", "-B", branch, f"origin/{branch}" if exists else "origin/main")
        if exists and run(["git", "merge", "--no-edit", "-q", "origin/main"], repo).returncode:
            git(repo, "merge", "--abort", check=False)
            raise PublishError("origin/main does not merge cleanly into the existing branch; owner decision needed")
        files = build_note(cfg, store, inv)
        leaked = secret_hits(cfg, files)
        if leaked:
            set_pub(store, inv, state="refused", reason=f"secret pattern in {', '.join(leaked)}: not published")
            return "refused"
        note = repo / NOTE_ROOT / lead_id
        if note.exists():
            shutil.rmtree(note)  # this directory belongs to this lead only; history keeps every earlier version
        for name, raw in files.items():
            (note / name).parent.mkdir(parents=True, exist_ok=True)
            (note / name).write_bytes(raw)
        rel = f"{NOTE_ROOT}/{lead_id}"
        git(repo, "add", "--", rel)
        if run(["git", "diff", "--cached", "--quiet"], repo).returncode == 0 and exists:
            set_pub(store, inv, state="draft_open" if pub["pr_number"] else pub["state"], reason="no change since the last publication")
            return "unchanged"
        audit = json.loads(pub["audit_json"])
        git(repo, "commit", "-q", "-m", f"triagent campaign: {(audit['title'] or lead_id)[:90]}\n\nLead {lead_id}, "
            f"investigation {inv}. Generated by the TriAgent campaign from audited missions; draft for owner review.")
        results = []
        for name, cmd in (*CHECKS, ("note_verify", [f"{rel}/verify.py"])):
            p = run([sys.executable, *cmd], repo, 900)  # the service interpreter, not the system 3.9 on its PATH
            results.append({"check": name, "code": p.returncode, "tail": (p.stdout + p.stderr)[-600:]})
        head = git(repo, "rev-parse", "HEAD")
        failed = [r["check"] for r in results if r["code"]]
        if failed:
            set_pub(store, inv, state="tests_failed", head_sha=head, checks_json=canonical(results),
                    reason=f"checks failed: {', '.join(failed)}; nothing pushed")
            return "tests_failed"
        push = run(["git", "push", "-q", "origin", f"HEAD:refs/heads/{branch}"], repo, 600)  # a normal push, no force flag
        if push.returncode:
            raise PublishError(f"push refused: {push.stderr[-300:]}")
        body = pr_body(audit, lead_id, inv, results)
        (repo / ".git" / "triagent-pr-body.md").write_text(body)
        if pub["pr_number"]:
            run([gh_bin(cfg), "pr", "edit", str(pub["pr_number"]), "--body-file", str(repo / ".git" / "triagent-pr-body.md")], repo)
            number, url = pub["pr_number"], pub["pr_url"]
        else:
            p = run([gh_bin(cfg), "pr", "create", "--draft", "--base", "main", "--head", branch, "--title",
                     f"Campaign: {(audit['title'] or lead_id)[:100]}", "--body-file", str(repo / ".git" / "triagent-pr-body.md")], repo)
            m = re.search(r"https://github\.com/\S+/pull/(\d+)", p.stdout)
            if p.returncode or not m:
                raise PublishError(f"branch pushed, PR not created: {(p.stderr or p.stdout)[-300:]}")
            number, url = int(m.group(1)), m.group(0)
        set_pub(store, inv, state="draft_open", pr_number=number, pr_url=url, head_sha=head, checks_json=canonical(results),
                source_sha256=sha256_bytes(b"".join(files[k] for k in sorted(files))), reason="draft PR open, owner review")
        store.log("publish", f"{inv}: draft PR #{number} at {head[:10]}")
        return "draft_open"
    except (PublishError, subprocess.TimeoutExpired, OSError) as exc:
        set_pub(store, inv, state="push_failed", reason=str(exc)[:600])
        store.log("publish", f"{inv}: {exc}", level="warning")
        return "push_failed"


def pr_body(audit: dict, lead_id: str, inv: str, results: list[dict]) -> str:
    return "\n".join([
        f"Draft from the TriAgent historical campaign (lead `{lead_id}`, investigation `{inv}`). Not merged; the owner "
        "decides. Generated by the campaign (Claude Code on-chain missions, Codex review and audit, Grok X search).", "",
        "## Summary", "", audit["summary"], "", "## Published facts", "",
        *[f"- [{c['tier']}] {c['statement']}" for c in audit["kept_claims"]], "",
        f"Dropped by the evidence gate: {len(audit['dropped_claims'])} claim(s).", "", "## Not demonstrated", "",
        *[f"- {x}" for x in audit["not_demonstrated"]], "", "## Checks (all passed before push)", "",
        *[f"- `{r['check']}`: exit {r['code']}" for r in results], "",
        f"Files: `{NOTE_ROOT}/{lead_id}/` only. README and protected evidence unchanged."])


# ---------------------------------------------------------------- maintenance
def sync_prs(cfg: Config, store: Store) -> None:
    """Merged or closed by the owner: recorded, so the next update opens no second PR on a closed one."""
    for p in store.query("SELECT investigation, pr_number FROM publications WHERE state='draft_open' AND pr_number IS NOT NULL"):
        out = run([gh_bin(cfg), "pr", "view", str(p["pr_number"]), "--json", "state"], cfg.state_dir / "publish-repo", 60)
        if out.returncode == 0 and json.loads(out.stdout or "{}").get("state") in ("MERGED", "CLOSED"):
            set_pub(store, p["investigation"], state="closed", reason=f"PR {json.loads(out.stdout)['state'].lower()} by the owner")


def tick(cfg: Config, store: Store) -> str:
    """From the maintenance step: at most one publication at a time, in its own thread."""
    if not cfg.live or cfg.get("PUBLISH_ENABLED") != "1" or LOCK.locked():
        return ""
    open_prs = store.query("SELECT count(*) n FROM publications WHERE state='draft_open'")[0]["n"]
    row = store.query("SELECT investigation FROM publications WHERE state='prepared' OR (state='push_failed' AND "
                      "attempts<3 AND updated<?) ORDER BY updated LIMIT 1", (now() - 3600,))  # a network failure: 3 tries
    sync_due = now() - int(store.get_kv("publish.synced") or 0) > 3600 and open_prs
    if not row and not sync_due:
        return ""
    if row and open_prs >= cfg.int("PUBLISH_MAX_OPEN") and not store.query(
            "SELECT 1 FROM publications WHERE investigation=? AND pr_number IS NOT NULL", (row[0]["investigation"],)):
        set_pub(store, row[0]["investigation"], reason=f"waiting: {open_prs} campaign draft PRs already open")
        row = []

    def work():
        with LOCK:
            try:
                if sync_due:
                    store.set_kv("publish.synced", now())
                    sync_prs(cfg, store)
                if row:
                    publish(cfg, store, row[0]["investigation"])
            except Exception as exc:  # recorded; the row keeps its state for the next attempt
                store.log("publish", f"publisher crashed: {exc}", level="error")
    threading.Thread(target=work, name="publisher", daemon=True).start()
    return row[0]["investigation"] if row else "sync"
