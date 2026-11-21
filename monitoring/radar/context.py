"""Attach the reviewed public evidence that a PolySentinel archive had received by alert emission."""
import hashlib
import json
import math
from pathlib import Path
from runpy import run_path
import sqlite3
from urllib.parse import urlsplit
import zlib

# Load the two standalone archived modules without writing bytecode inside their evidence manifests.
ARCHIVE = Path(__file__).resolve().parents[2] / "investigations/polysentinel/sources/polysentinel"
storage = run_path(str(ARCHIVE / "db.py"))
encode = storage["encode"]
register_functions = storage["register_functions"]
public_timing = run_path(str(ARCHIVE / "news.py"))["public_timing"]


def latest(db, kind, key, cutoff):
    rows = db.execute(
        "SELECT payload, observed_at FROM history WHERE kind=? AND key=? AND observed_at<=? "
        "ORDER BY observed_at DESC LIMIT 2", (kind, key, cutoff)).fetchall()
    if not rows or (len(rows) == 2 and rows[0][1] == rows[1][1] and rows[0][0] != rows[1][0]):
        return None
    return {"payload": json.loads(rows[0][0]), "observed_at": rows[0][1]}


def assessment(db, record):
    emitted, trigger = record.get("emitted_t"), record.get("trigger_t")
    condition = str(record["market"].get("condition_id") or "").lower()
    response = {"alert": record["id"], "condition_id": condition, "as_of": emitted,
                "status": "unknown", "scope": "reviewed event-level public sources"}
    if (not condition or not all(type(t) in (int, float) and math.isfinite(t) for t in (trigger, emitted))
            or trigger > emitted):
        return response
    # The key is a Gamma market ID. An old association can be revised before the cutoff.
    keys = db.execute("SELECT DISTINCT key FROM history WHERE kind='market' AND observed_at<=? "
                      "AND lower(json_extract(payload,'$.condition_id'))=?", (emitted, condition))
    event_ids = set()
    for (k,) in keys:
        market = latest(db, "market", k, emitted)
        if not market:
            return response
        m = market["payload"]
        if str(m.get("condition_id") or "").lower() == condition and m.get("event_id"):
            event_ids.add(str(m["event_id"]))
    if len(event_ids) != 1:
        return response
    event = event_ids.pop()
    response["event_id"] = event
    evidence = latest(db, "public_milestone", event, emitted)
    if not evidence:
        return response
    p = evidence["payload"]
    if (str(p.get("event_id", event)) != event or p.get("verified") is not True or p.get("result_available") is not True
            or (p.get("condition_ids") is not None and condition not in [str(x).lower() for x in p["condition_ids"]])):
        return response
    timing = public_timing(evidence, trigger, emitted)
    if timing["status"] == "unknown":
        return response
    row = db.execute("SELECT r.source,r.params,r.status,r.observed_at,r.content_id,c.body "
                     "FROM response_refs r JOIN contents c ON c.id=r.content_id WHERE r.id=?",
                     (p["evidence_id"],)).fetchone()
    if not row:
        return response
    source, params, status, seen, sha, body = row
    if (source != p["source_url"] or urlsplit(source).scheme != "https" or status != 200
            or not p["public_at"] <= seen <= evidence["observed_at"]):
        return response
    raw = zlib.decompress(body)
    # Store hashes the original JSON number. SQLite REAL returns 125 and 125.0 alike.
    clocks = (seen, int(seen)) if seen.is_integer() else (seen,)
    reference = p["evidence_id"]
    matching_id = any(hashlib.sha256(encode([source, json.loads(params), status, t]).encode() + raw).hexdigest()
                      == reference for t in clocks)
    if not raw or hashlib.sha256(raw).hexdigest() != sha or not matching_id:
        return response
    return {**response, "status": timing["status"], "milestone_type": p.get("milestone_type"),
            "public_at": p["public_at"], "source_url": source, "received_at": seen,
            "reviewed_at": evidence["observed_at"], "source_sha256": sha, "evidence_id": reference}


def for_alert(alert_file, alert_id, archive):
    from radar import chain
    _, _, errors = chain.verify(alert_file)
    if errors:
        raise ValueError("alert chain failed verification")
    records = [r for _, r in chain.read(alert_file) if r.get("id") == alert_id]
    if len(records) != 1:
        raise ValueError("expected exactly one sealed alert with this ID")
    db = sqlite3.connect(Path(archive).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.execute("BEGIN")
        if db.execute("PRAGMA user_version").fetchone()[0] != 2:
            raise ValueError("expected a PolySentinel v2 archive")
        register_functions(db)
        return assessment(db, records[0])
    finally:
        db.close()
