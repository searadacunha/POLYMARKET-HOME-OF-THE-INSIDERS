"""A radar alert: one alert of phi_engine, sealed once with everything a reviewer needs to judge it later.

The engine decides; this module only describes. It adds what the engine's record does not say explicitly: which
inputs were available at the trigger and which were not (`DATA_UNAVAILABLE`), the evidence level of each claim the
alert implies, the class's out-of-sample result and its uncertainty, the recent load of the same class, and a
fingerprint of this code. A radar alert is always an `ANOMALY`: suspicion needs a human review, proof is never
automatic. Nothing about the outcome of the market can be in a record: it is built before the outcome exists and is
never rewritten (`chain.py`)."""
import hashlib, os, time

SCHEMA = "radar-alert/1"
DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
LEVELS = ("CONFIRMED", "SUPPORTED", "HYPOTHESIS", "REFUTED", "UNRESOLVED")
GROUP = {"C4_COFUNDED_GROUP", "C5_RECURRENT_FUNDER"}
UNSURE_PAYER = {None, "historical state unavailable", "tags unavailable"}
HERE = os.path.dirname(os.path.abspath(__file__))


def fingerprint(folder=HERE):
    """SHA-256 of this package's .py files (relative path, NUL, bytes; CRLF read as LF), and their number."""
    h, n = hashlib.sha256(), 0
    for name in sorted(f for f in os.listdir(folder) if f.endswith(".py") and not f.startswith((".", "#"))):
        with open(os.path.join(folder, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read().replace(b"\r\n", b"\n")); n += 1
    return {"radar_code_sha256": h.hexdigest(), "files_hashed": n, "schema": SCHEMA}


def utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def _cluster(cls, w):
    link = w.get("linked_wallet") or {}
    if cls not in GROUP or not isinstance(link, dict) or not link.get("root"):
        return None
    return {"key": link["root"], "members_known_at_trigger": sorted({w["wallet"], link.get("other")} - {None}),
            "basis": "a plain key behind a deposit of each wallet (receipt path); this is a funding relationship, not a common owner"}


def inputs_at_trigger(a, book=None):
    """State of each input the decision could use, as the engine recorded it."""
    ev = a.get("evidence") or {}
    dq, fills, deps = ev.get("data_quality") or {}, ev.get("fills") or [], (a.get("wallets") or {}).get("deposits") or []
    return {
        "fills": "OK" if fills else DATA_UNAVAILABLE,
        "wallet_history": "OK" if dq.get("history_complete") else "CAPPED_AT_1000_ROWS",
        "funding_payers": ("NONE_IN_24H" if not deps else "UNRESOLVED" if any(d.get("payer_kind") in UNSURE_PAYER for d in deps) else "OK"),
        "payer_public_tags": "READ_AT_ALERT_TIME" if deps else "NOT_NEEDED",
        "order_book_depth": "OK" if book else DATA_UNAVAILABLE,
        "first_public_information": DATA_UNAVAILABLE,
    }


def claims(a):
    """Evidence level of each statement an alert could be read as making."""
    cls, ev = a["class"], a.get("evidence") or {}
    deps = (a.get("wallets") or {}).get("deposits") or []
    out = [{"claim": "the listed fills happened on chain, in these transactions", "level": "CONFIRMED" if ev.get("fills") else "UNRESOLVED",
            "basis": "OrderFilled logs: transaction, log index, block"}]
    if deps:
        sure = all(d.get("payer_kind") not in UNSURE_PAYER for d in deps)
        out.append({"claim": "the deposits were paid by the apparent payers listed", "level": "SUPPORTED" if sure else "UNRESOLVED",
                    "basis": "payer read from each deposit's receipt; a fungible balance is not traced to one owner"})
    if cls in GROUP:
        out.append({"claim": "the linked wallets were funded by the same plain key", "level": "SUPPORTED",
                    "basis": "receipt-guarded links only (receipt_guard_v1)"})
        out.append({"claim": "the linked wallets have one controller", "level": "HYPOTHESIS",
                    "basis": "a shared funder is compatible with one person, a group with a treasurer, or a service not yet recognised"})
    out.append({"claim": "the trader acted on private information", "level": "HYPOTHESIS",
                "basis": "public data cannot establish it; the class's out-of-sample result is in `controls`"})
    return out


def build(a, line_sha256, now, load_24h=None, book=None):
    """a: one parsed line of phi_engine's <db>.alerts.jsonl; line_sha256: SHA-256 of that line's bytes."""
    w, m, v = a.get("wallets") or {}, a.get("market") or {}, a.get("validation") or {}
    readings = (a.get("anomaly") or {}).get("readings") or {}
    ev = a.get("evidence") or {}
    rec = {
        "schema": SCHEMA, "kind": "ANOMALY",
        "id": hashlib.sha256(f"{a['id']}|{line_sha256}".encode()).hexdigest()[:24],
        "engine_alert_id": a["id"], "engine_line_sha256": line_sha256,
        "trigger_t": a.get("t_alert"), "trigger_utc": a.get("t_alert_utc"), "emitted_at_utc": a.get("detected_at_utc"), "sealed_at_utc": utc(now),
        "market": {"question": m.get("title"), "outcome": m.get("outcome"), "condition_id": m.get("condition_id"),
                   "event_slug": m.get("event_slug"), "family": m.get("family"), "protocol_version": m.get("protocol_version"),
                   "scheduled_end_utc": m.get("scheduled_end_utc")},
        "wallets": [x for x in [w.get("wallet")] + [((w.get("linked_wallet") or {}).get("other"))] if x],
        "cluster": _cluster(a["class"], w),
        "transactions": {"fills": ev.get("fills") or [], "deposits": w.get("deposits") or [],
                         "deposit_receipts": ev.get("deposit_receipts") or []},
        "sources": ["Polygon OrderFilled logs", "Polymarket data API v2/activity", "Gamma market catalogue", "Polygon receipts and archive state",
                    "Blockscout public tags (read at alert time)"],
        "information_at_trigger": {"inputs": inputs_at_trigger(a, book), "signals": (a.get("anomaly") or {}).get("signals"),
                                   "readings": readings},
        "risk": {"class": a["class"], "rule": (a.get("anomaly") or {}).get("what"),
                 "method": "a yes/no rule fixed in advance; no single score and no probability",
                 "rarity_score": readings.get("rarity")},
        "controls": {"out_of_sample": {k: v.get(k) for k in ("status", "study_verdict", "summary", "alert_events", "excess", "t1_p", "t2_p")},
                     "same_class_alerts_last_24h": load_24h},
        "uncertainty": {"class_excess_95ci": v.get("excess_ci"),
                        "note": "the interval of the class on validation events; there is no per-account probability"},
        "data_latency": {"seconds_from_trade_to_alert": a.get("seconds_from_trade_to_alert"), "fills_read_at": "finalized blocks"},
        "detector": {"engine": a.get("detector"), "radar": fingerprint()},
        "price_and_depth": {"price_at_alert": m.get("price_at_alert"), "price_one_hour_before": (readings.get("timing") or {}).get("price_one_hour_before"),
                            "depth": book if book else DATA_UNAVAILABLE},
        "evidence_status": claims(a),
        "other_explanations": (a.get("anomaly") or {}).get("other_explanations"),
        "reading": a.get("reading"),
    }
    return rec
