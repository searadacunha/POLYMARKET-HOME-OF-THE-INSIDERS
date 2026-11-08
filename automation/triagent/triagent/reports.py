"""Investigation reports, the daily digest and operator notifications, built only from stored rows.

Nothing here calls a model. A mission report restates the stored GPT review, the supervisor's deterministic
checks and the rows they point to (findings, edges, evidence, follow-up missions); the daily digest reuses those
reports. Agent text is untrusted: it is flattened to one line per item so it cannot fake a heading, and every
page renders it as text.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import polymarket
from .store import canonical, now, sha256_bytes

# Preferences editable from the dashboard (kv "pref.<KEY>"), each with its validator; defaults in config.DEFAULTS.
PREFS = {
    "DAILY_REPORT_TIME": lambda v: bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v)),
    "DAILY_REPORT_TZ": lambda v: _tz_ok(v),
    "NOTIFY_ENABLED": lambda v: v in ("0", "1"),
    "NOTIFY_MAX_DAY": lambda v: v.isdigit() and int(v) <= 50,
    "NOTIFY_COOLDOWN_S": lambda v: v.isdigit() and int(v) <= 86400,
    "BLOCKED_NOTIFY_AFTER_S": lambda v: v.isdigit() and 600 <= int(v) <= 604800,
}
LINK_KINDS = ("DIRECT_TRANSFER", "SAME_FUNDER", "SAME_DEPOSIT_ADDRESS", "BRIDGE_ORDER")  # not shared services
# 6-decimal stables; pUSD is minted 1:1 in raw value against USDC (polymarket.py matches the two values exactly)
SIX_DECIMALS = {polymarket.USDC_E: "USDC.e", polymarket.USDC: "USDC", polymarket.COLLATERAL: "pUSD",
                "usdc": "USDC", "usdc.e": "USDC.e"}


def _tz_ok(name: str) -> bool:
    try:
        ZoneInfo(name)
        return True
    except Exception:
        return False


def pref(store, cfg, key: str) -> str:
    return store.get_kv("pref." + key) or cfg.get(key)


def link(cfg, route: str) -> str:
    return f"http://127.0.0.1:{cfg.get('HTTP_PORT')}/#/{route}"


def flat(text, limit: int = 600) -> str:
    """One line, bounded: agent text cannot open a new Markdown block inside a report."""
    s = " ".join(str(text or "").split())
    return s if len(s) <= limit else s[:limit - 1] + "…"


def words(text: str, limit: int) -> str:
    w = str(text or "").split()
    return " ".join(w[:limit]) + (" …" if len(w) > limit else "")


def amount(e: dict) -> str:
    sym = SIX_DECIMALS.get((e.get("token") or "").split(" ")[0].lower())
    raw = str(e.get("amount") or "")
    if sym and raw.isdigit():
        return f"{int(raw) / 1e6:,.2f} {sym}"
    return f"{raw} {e.get('token') or ''}".strip()


def iso(ts) -> str:
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else "inconnu"


# ---------------------------------------------------------------- mission report
def decision_fr(review: dict, established: list, refuted: list) -> str:
    d, n = review.get("decision", ""), int(review.get("enqueued") or 0)
    if d == "continue":
        return f"approfondir ({n} mission(s) de suivi créée(s))" if n else "poursuivre (aucune mission de suivi admise)"
    if d == "needs_human":
        return "suspendre (GPT demande une décision humaine)"
    if refuted and not established:
        return "réfuter (affirmations testées invalidées, aucune établie)"
    return {"stop_insufficient_basis": "suspendre (base insuffisante)",
            "stop_no_new_information": "clôturer (aucune information nouvelle)"}.get(d, d or "inconnue")


def mission_facts(store, job: dict) -> dict:
    """Everything a mission report says, as data (also used by the digest and the dashboard)."""
    review = json.loads(job["review_json"])
    claims = review.get("claims", [])
    novelty = int(review.get("novelty") or 0)
    by = lambda *t: [c for c in claims if c.get("tier") in t]  # noqa: E731
    established = by("CONFIRMED", "SUPPORTED")
    edges = store.query("SELECT * FROM edges WHERE job_id=? ORDER BY ts, id", (job["id"],))
    verified = [e for e in edges if e["level"] == "receipt_verified" and e["kind"] in LINK_KINDS]
    discovery = novelty >= 1 and bool(established)
    major = discovery and (novelty >= 4 or bool(by("CONFIRMED")) or bool(verified))
    return {"review": review, "claims": claims, "novelty": novelty, "established": established,
            "refuted": by("REFUTED"), "uncertain": by("HYPOTHESIS", "UNRESOLVED"), "edges": edges,
            "verified_links": verified, "discovery": discovery,
            "importance": "major" if major else ("normal" if discovery else "none")}


def mission_report(store, cfg, job_id: str) -> str | None:
    """Create the report of a reviewed mission once; returns its id (the existing one when already made)."""
    job = store.job(job_id)
    if not job or job["status"] != "done" or not job["review_json"]:
        return None
    source = sha256_bytes(job["review_json"].encode())
    found = store.query("SELECT id FROM reports WHERE kind='mission' AND subject=? AND source_sha256=?",
                        (job_id, source))
    if found:
        return found[0]["id"]
    f = mission_facts(store, job)
    review, claims = f["review"], f["claims"]
    inv = store.investigation(job["investigation"]) or {"id": job["investigation"], "title": "", "status": "?"}
    version = store.query("SELECT count(*) n FROM reports WHERE kind='mission' AND subject=?", (job_id,))[0]["n"] + 1
    when = job["finished"] or job["updated"]
    rid = f"RPT-{datetime.fromtimestamp(when, timezone.utc).strftime('%Y%m%d')}-{job_id[:8]}-v{version}"
    stored = json.loads(job["result_json"] or "{}")
    checks = review.get("checks", {})
    cited = sorted({e for c in claims for e in c.get("evidence_ids", []) if isinstance(e, str)})
    ev = {r["sha256"]: r for r in store.query(
        "SELECT sha256, source, ref FROM evidence WHERE sha256 IN (SELECT value FROM json_each(?))", (canonical(cited),))}
    children = store.query("SELECT id, agent, kind, task, falsifier, status FROM jobs WHERE parent=? ORDER BY created",
                           (job_id,))
    rows = lambda t: [r["text"] for r in store.query(  # noqa: E731
        "SELECT text FROM findings WHERE job_id=? AND type=? ORDER BY id", (job_id, t))]

    def claim_line(c, objection=False):
        ids = [e for e in c.get("evidence_ids", []) if isinstance(e, str)]
        refs = "; ".join(f"`{e[:12]}…` {flat(ev[e]['ref'], 140)}" if e in ev else f"`{flat(e, 90)}`" for e in ids[:4])
        extra = f" — objection GPT : {flat(c.get('objection'), 300)}" if objection and c.get("objection") else ""
        return f"- [{c.get('tier')}] {flat(c.get('statement'))}" + (f" — preuves : {refs}" if refs else "") + extra

    counts = ", ".join(f"{len([c for c in claims if c.get('tier') == t])} {t}" for t in
                       ("CONFIRMED", "SUPPORTED", "HYPOTHESIS", "UNRESOLVED", "REFUTED"))
    summary = words(("" if f["discovery"] else "Aucune découverte nouvelle. ")
                    + f"Nouveauté {f['novelty']}/5 selon la revue GPT. Affirmations revues : {counts}. "
                    f"Liens financiers rapportés : {len(f['edges'])}, dont {len(f['verified_links'])} vérifiés par reçu. "
                    + flat(review.get("analysis"), 3000), 150)
    if f["discovery"]:
        found_lines = [claim_line(c) for c in f["established"]]
    else:
        found_lines = [f"Aucune découverte nouvelle : nouveauté {f['novelty']}/5 ({flat(review.get('novelty_reason'), 300)})."]
        if f["established"]:
            found_lines.append(f"- {len(f['established'])} affirmation(s) déjà connue(s) reconfirmée(s), non comptée(s) comme découverte.")
    groups = (("Transferts directs et ordres de pont", ("DIRECT_TRANSFER", "BRIDGE_ORDER")),
              ("Financements communs", ("SAME_FUNDER",)),
              ("Destinations documentées et services mutualisés", ("SAME_DEPOSIT_ADDRESS", "SHARED_SERVICE")),
              ("Corrélations et hypothèses", ("TEMPORAL_CORRELATION", "HYPOTHESIS")))
    money = []
    for label, kinds in groups:
        sel = [e for e in f["edges"] if e["kind"] in kinds]
        if sel:
            money.append(f"- {label} :")
            money += [f"  - `{e['src']}` → `{e['dst']}` · {amount(e)} · {e['chain']} tx `{e['tx_hash'] or 'aucune'}` · "
                      f"{iso(e['ts'])} · niveau **{e['level']}** · {flat(e['method'], 160)}" for e in sel[:25]]
    refuted = [claim_line(c, True) for c in f["refuted"]] + [f"- {flat(t)}" for t in rows("negative")]
    uncertain = ([claim_line(c, True) for c in f["uncertain"]] + [f"- Question ouverte : {flat(q)}" for q in rows("question")]
                 + [f"- Risque signalé par GPT : {flat(r, 300)}" for r in review.get("risks", [])])
    dup = review.get("duplicates_existing") or []
    importance = [f"Nouveauté {f['novelty']}/5 selon la revue GPT : {flat(review.get('novelty_reason'), 500)}"]
    if dup:
        importance.append("Recoupe des travaux existants : " + "; ".join(flat(d, 160) for d in dup[:5]))
    importance.append(f"Ce que cela change : l'enquête est {'ouverte' if inv.get('status') == 'open' else 'arrêtée (' + str(inv.get('status')) + ')'}"
                      f" ; cohérence temporelle selon GPT : {flat(review.get('temporal_consistency'), 300)}")
    nxt = [f"- **{c['agent']}** ({c['kind']}, `{c['id']}`, statut {c['status']}) — Objectif : {flat(c['task'], 500)} — "
           f"Test de falsification : {flat(c['falsifier'], 400) or 'non précisé'}" for c in children]
    if not nxt:
        nxt = ["Aucune mission de suivi créée."]
        tests = review.get("falsification_tests") or []
        if tests:
            nxt.append("Tests de falsification proposés par GPT, non planifiés : " + "; ".join(flat(t, 200) for t in tests[:5]))
    prov = review.get("_provider") or {}
    evc = checks.get("evidence") or {}
    sources = [f"- Mission `{job_id}` : MISSION.md SHA-256 `{job['context_sha256'] or 'non enregistré'}` ; résultat brut "
               f"SHA-256 `{job['result_sha256']}` ; revue GPT stockée SHA-256 `{source}`",
               f"- Revue GPT : mode {prov.get('mode', cfg.get('OPENAI_MODE'))}, requête `{prov.get('request_id', 'non enregistrée')}`"
               + (f", réponse SHA-256 `{prov['answer_sha256']}`" if prov.get("answer_sha256") else "")]
    if evc:
        sources.append(f"- Contrôle déterministe des preuves : {evc.get('cited', 0)} citées, {len(evc.get('verified', []))} "
                       f"vérifiées octet par octet, manquantes : {', '.join(evc.get('missing', [])) or 'aucune'}")
    posts = {str(x) for p in checks.get("x_posts", []) for x in (p.get("post_id"), p.get("post_url"))}
    sources += [f"- Preuve `{e}` : {ev[e]['source']} {flat(ev[e]['ref'], 300)}" if e in ev else
                f"- Identifiant cité `{flat(e, 120)}` : pas de copie archivée sous cette empreinte (transaction, marché ou "
                "document cité par l'agent, non rejoué)" for e in cited if e not in posts]
    sources += [f"- Transaction {e['chain']} `{e['tx_hash']}` (preuve `{e['evidence_sha256'] or 'aucune'}`)"
                for e in f["edges"] if e["tx_hash"]]
    sources += [f"- Post X {flat(p.get('post_url'), 200)} ({p.get('author')}, {p.get('created_at')}, relu par le "
                f"superviseur : {'oui' if p.get('verified') else 'non'})" for p in checks.get("x_posts", [])]
    title = f"{'Mission sans découverte' if not f['discovery'] else 'Découverte'} — {flat(inv.get('title'), 90)}"
    body = "\n".join([
        f"### RAPPORT D'INVESTIGATION — {iso(when)} / {rid}", "",
        f"**Enquête :** {flat(inv.get('title'), 300)} (`{inv['id']}`)", "",
        f"**Mission :** `{job_id}` · {job['agent']}/{job['kind']} · origine {job['origin']}"
        + (f" · suite de `{job['parent']}`" if job["parent"] else "") + f" · profondeur {job['depth']} · version {version}", "",
        f"**Résumé :** {summary}", "",
        "**Nouvelles découvertes :**", *found_lines, "",
        "**Relations financières :**", *(money or ["Aucune relation financière rapportée par cette mission."]), "",
        "**Hypothèses réfutées :**", *(refuted or ["Aucune."]), "",
        "**Points incertains :**", *(uncertain or ["Aucun."]), "",
        "**Importance :** " + " ".join(importance), "",
        f"**Décision de GPT :** {decision_fr(review, f['established'], f['refuted'])} (`{review.get('decision')}`)", "",
        "**Prochaines missions :**", *nxt, "",
        "**Sources :**", *sources, "",
        f"_Mission non revue par un humain. Rapport généré sans appel à une IA, à partir de la revue stockée. Résumé brut de "
        f"l'agent (non vérifié) : {flat(stored.get('report', {}).get('summary'), 400) or 'aucun'}_"])
    with store.conn(immediate=True) as c:
        c.execute("""INSERT OR IGNORE INTO reports(id,kind,subject,version,source_sha256,investigation,created,
                     period_start,period_end,importance,title,body_md,sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (rid, "mission", job_id, version, source, inv["id"], now(), job["started"], when, f["importance"],
                   title, body, sha256_bytes(body.encode())))
    return rid


# ---------------------------------------------------------------- daily digest
def due_slot(store, cfg, t: int | None = None) -> tuple[str, int]:
    """(local date, timestamp) of the latest digest time at or before t."""
    tz = ZoneInfo(pref(store, cfg, "DAILY_REPORT_TZ"))
    hh, mm = (int(x) for x in pref(store, cfg, "DAILY_REPORT_TIME").split(":"))
    local = datetime.fromtimestamp(t or now(), tz)
    slot = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if local < slot:
        slot -= timedelta(days=1)
    return slot.date().isoformat(), int(slot.timestamp())


def daily_digest(store, cfg, t: int | None = None) -> str | None:
    """At most one digest per local date, covering only what happened since the previous one. No model call."""
    t = t or now()
    day, slot = due_slot(store, cfg, t)
    if store.query("SELECT 1 FROM reports WHERE kind='daily' AND subject=?", (day,)):
        return None
    if slot < int(store.get_kv("center_installed") or 0):
        return None  # no back-dated digest for a slot that passed before the center was installed
    prev = store.query("SELECT max(period_end) e FROM reports WHERE kind='daily'")[0]["e"]
    start = int(prev or slot - 86400)
    reps = store.query("SELECT id, subject, title, importance FROM reports WHERE kind='mission' AND period_end>? AND "
                       "period_end<=? ORDER BY period_end", (start, t))
    found, progressing = [], {}
    for r in reps:
        job = store.job(r["subject"])
        facts = mission_facts(store, job)
        if facts["discovery"]:
            found += [f"- {flat(c['statement'], 400)} [{c['tier']}] — rapport {r['id']}" for c in facts["established"][:5]]
            progressing[job["investigation"]] = facts["novelty"]
    links = store.query("SELECT * FROM edges WHERE job_id IS NOT NULL AND level='receipt_verified' AND created>? AND "
                        "created<=? AND kind IN (SELECT value FROM json_each(?)) ORDER BY created",
                        (start, t, canonical(list(LINK_KINDS))))
    collected = store.query("SELECT count(*) n FROM edges WHERE job_id IS NULL AND created>? AND created<=?", (start, t))[0]["n"]
    refuted = store.query("SELECT text, job_id FROM findings WHERE created>? AND created<=? AND (type='negative' OR "
                          "(type='claim' AND tier='REFUTED')) ORDER BY id LIMIT 15", (start, t))
    stuck = store.query("SELECT id, agent, status, status_reason FROM jobs WHERE status IN ('blocked','failed') AND "
                        "updated>? ORDER BY updated DESC LIMIT 10", (start,))
    holds = [(p, json.loads(store.get_kv(f"hold_{p}") or "{}")) for p in ("claude", "openai", "xai")]
    holds = [f"- {p} en attente jusqu'à {iso(h['until'])} : {flat(h.get('reason'), 200)}" for p, h in holds
             if h and h.get("until", 0) > t]
    queued = store.query("SELECT id, agent, task, falsifier, priority, investigation FROM jobs WHERE status='queued' "
                         "ORDER BY priority DESC, created LIMIT 5")
    tests = store.query("SELECT text FROM findings WHERE type='test' AND created>? AND created<=? ORDER BY id DESC LIMIT 5",
                        (start, t))
    alerts = store.query("SELECT count(*) n, sum(level='HIGH') high FROM alerts WHERE created>? AND created<=?", (start, t))[0]
    done = store.query("SELECT count(*) n FROM jobs WHERE status='done' AND finished>? AND finished<=?", (start, t))[0]["n"]
    nothing = not found and not links
    lines = [f"### BILAN QUOTIDIEN — {day} / DAY-{day.replace('-', '')}", "",
             f"**Période :** {iso(start)} → {iso(t)} (depuis le bilan précédent)", "",
             f"**Activité :** {done} mission(s) terminée(s), {len(reps)} rapport(s) de mission, {alerts['n']} nouvelle(s) "
             f"alerte(s) dont {alerts['high'] or 0} HIGH (signaux non vérifiés), {collected} lien(s) de financement relevé(s) "
             "par le collecteur.", ""]
    if nothing:
        lines += ["**Découvertes :** Aucune découverte nouvelle depuis le bilan précédent.", ""]
    else:
        lines += ["**Ce qui a été réellement découvert :**", *(found or ["Aucune affirmation nouvelle établie."]), "",
                  "**Nouvelles connexions financières vérifiées :**",
                  *([f"- `{e['src']}` → `{e['dst']}` · {e['kind']} · {amount(e)} · tx `{e['tx_hash']}` (mission `{e['job_id']}`)"
                     for e in links[:20]] or ["Aucune."]), ""]
    lines += ["**Hypothèses abandonnées :**", *([f"- {flat(r['text'], 300)} (mission `{r['job_id']}`)" for r in refuted]
                                                 or ["Aucune."]), ""]
    if progressing:
        lines += ["**Enquêtes qui progressent :**", *[f"- `{i}` : nouveauté {n}/5" for i, n in progressing.items()], ""]
    lines += ["**Agents bloqués :**", *([f"- {s['agent']} `{s['id']}` {s['status']} : {flat(s['status_reason'], 200)}"
                                         for s in stuck] + holds or ["Aucun."]), ""]
    if not nothing or queued:
        lines += ["**Pistes les plus prometteuses (missions en file, par gain attendu) :**",
                  *([f"- [{q['priority']}/5] {q['agent']} `{q['id']}` : {flat(q['task'], 300)}" for q in queued] or ["Aucune."]), "",
                  "**Priorités scientifiques du prochain cycle :**",
                  *([f"- Falsifier : {flat(q['falsifier'], 300)}" for q in queued if q["falsifier"]]
                    + [f"- Test proposé par GPT : {flat(x['text'], 300)}" for x in tests] or ["Aucune priorité nouvelle."]), ""]
    from . import campaign  # campaign imports reports lazily too: no import cycle at load time
    if campaign.state(store) != "off":
        c = campaign.summary(store)
        prs = store.query("SELECT state, count(*) n FROM publications GROUP BY state")
        lines += [f"**Campagne historique :** {c['state']}, passe {c['pass']}, {c['cells_searched_this_pass']}/"
                  f"{c['cells_total']} cellules cherchées, pistes {canonical(c['leads'])}, publications "
                  f"{canonical({r['state']: r['n'] for r in prs})}.", ""]
    lines.append("_Bilan construit à partir des revues GPT déjà stockées, sans nouvelle session d'IA._")
    body = "\n".join(lines)
    importance = "major" if any(r["importance"] == "major" for r in reps) else ("none" if nothing else "normal")
    rid = f"DAY-{day.replace('-', '')}"
    with store.conn(immediate=True) as c:
        c.execute("""INSERT OR IGNORE INTO reports(id,kind,subject,version,source_sha256,investigation,created,
                     period_start,period_end,importance,title,body_md,sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (rid, "daily", day, 1, sha256_bytes(body.encode()), None, t, start, t, importance,
                   f"Bilan du {day}" + (" — aucune découverte" if nothing else ""), body, sha256_bytes(body.encode())))
    return rid


# ---------------------------------------------------------------- notifications
def notify(store, cfg, kind: str, key: str, title: str, message: str, route: str, sender) -> bool:
    """Deduplicated by key; then the switch, daily quota and per-kind cooldown. Every decision is recorded."""
    if store.query("SELECT 1 FROM notifications WHERE key=?", (key,)):
        return False
    day = now() - now() % 86400
    reason = ""
    if not cfg.live:
        reason = "dry run: a simulation never notifies"
    elif pref(store, cfg, "NOTIFY_ENABLED") != "1":
        reason = "notifications disabled in settings"
    elif store.query("SELECT count(*) n FROM notifications WHERE sent=1 AND created>=?", (day,))[0]["n"] >= \
            int(pref(store, cfg, "NOTIFY_MAX_DAY")):
        reason = "daily notification quota reached"
    elif store.query("SELECT 1 FROM notifications WHERE kind=? AND sent=1 AND created>?",
                     (kind, now() - int(pref(store, cfg, "NOTIFY_COOLDOWN_S")))):
        reason = f"cooldown for {kind}"
    url = link(cfg, route)
    sent = False
    if not reason:
        sent = bool(sender(title, message, link=url))
        reason = "" if sent else "notifier failed"
    store.execute("INSERT OR IGNORE INTO notifications(key,kind,created,title,message,link,sent,reason) "
                  "VALUES (?,?,?,?,?,?,?,?)", (key, kind, now(), title[:120], message[:400], url, int(sent), reason))
    return sent


def notify_pending(store, cfg, sender, gate: str = "") -> int:
    """Only what appeared after the center was installed: a backfill never floods the screen."""
    since, sent = int(store.get_kv("center_installed") or now()), 0
    for r in store.query("SELECT id, title FROM reports WHERE importance='major' AND period_end>?", (since,)):
        sent += notify(store, cfg, "report", f"report:{r['id']}", "TriAgent : rapport majeur",
                       flat(r["title"], 200), f"reports/{r['id']}", sender)
    for e in store.query("SELECT e.job_id, j.investigation, count(*) n FROM edges e JOIN jobs j ON j.id=e.job_id WHERE "
                         "e.level='receipt_verified' AND e.created>? AND e.kind IN (SELECT value FROM json_each(?)) "
                         "GROUP BY e.job_id", (since, canonical(list(LINK_KINDS)))):
        sent += notify(store, cfg, "connection", f"connection:{e['job_id']}", "TriAgent : connexion financière vérifiée",
                       f"{e['n']} lien(s) vérifié(s) par reçu dans la mission {e['job_id'][:8]}",
                       f"investigations/{e['investigation']}", sender)
    late = now() - int(pref(store, cfg, "BLOCKED_NOTIFY_AFTER_S"))
    for j in store.query("SELECT id, agent, updated, status_reason FROM jobs WHERE status='blocked' AND updated<? AND "
                         "updated>?", (late, since)):
        sent += notify(store, cfg, "blocked", f"blocked:{j['id']}:{j['updated']}", "TriAgent : mission bloquée",
                       f"{j['agent']} {j['id'][:8]} : {flat(j['status_reason'], 200)}", "agents", sender)
    for p in ("claude", "openai", "xai"):
        h = json.loads(store.get_kv(f"hold_{p}") or "{}")
        if h.get("until", 0) > now() and str(h.get("reason", "")).startswith("auth"):
            sent += notify(store, cfg, "blocked", f"auth:{p}:{now() // 86400}", f"TriAgent : {p} non connecté",
                           flat(h["reason"], 200), "agents", sender)
    if gate and gate != "paused":  # an operator pause is a choice, not a blockage
        first = int(store.get_kv("gate_since") or 0) or now()
        store.set_kv("gate_since", first)
        if first < late:
            sent += notify(store, cfg, "blocked", f"gate:{first}", "TriAgent : orchestration arrêtée", gate, "agents", sender)
    else:
        store.execute("DELETE FROM kv WHERE key='gate_since'")
    return sent


def tick(store, cfg, sender, gate: str = "") -> dict:
    """Once a minute from the supervisor's maintenance step (both orchestrators)."""
    if now() - int(store.get_kv("center_tick") or 0) < 60:
        return {}
    store.set_kv("center_tick", now())
    if not store.get_kv("center_installed"):
        store.set_kv("center_installed", now())
    made = [mission_report(store, cfg, r["id"]) for r in store.query(
        "SELECT id FROM jobs WHERE status='done' AND review_json IS NOT NULL AND id NOT IN "
        "(SELECT subject FROM reports WHERE kind='mission')")]
    return {"reports": len(made), "daily": daily_digest(store, cfg), "notified": notify_pending(store, cfg, sender, gate)}
