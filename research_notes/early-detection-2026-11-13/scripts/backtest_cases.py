"""Chronological replay of the documented cases through the monitor (network needed).

    python3 research_notes/early-detection-2026-11-13/scripts/backtest_cases.py WORK_DB OUT_JSON

For each case of the two registries in audit/, up to MAX_PER_CASE markets are replayed from 13 days before the end of
the case to its end. The end is the first public information when the registry holds a sourced time, else the
resolution. The replay advances by ten minutes and reads a wallet's history only as of its own first buy, exactly as
the live monitor would. A market whose tape needs more than 300 pages is reported as too deep, never as "no alert".

The result says whether the tested pattern appears in a case, when, and whether the account it points at is one the
case file already names. A case with no alert is a case of another kind, not a clean bill for anyone.
"""
import calendar, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "monitoring"))
from phi_monitor import collect, detect, net, store   # noqa: E402

AUDIT = os.path.join(HERE, "..", "audit")
MAX_PER_CASE = 6
WINDOW = 13 * 86400
SKIP = {"C5", "MAD-2026-01-03-JAN31", "IRAN-2026-02-28-STRIKES", "IRAN-2025-06-13-ISRAEL-BY-FRIDAY", "CATALOGUE-RELATED-MARKETS"}   # same markets as C1, C4, C3, or no claim


def ts(iso):
    if not iso or not isinstance(iso, str) or len(iso) < 19 or iso[4] != "-":
        return None
    return calendar.timegm(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))


def cases():
    for folder in ("ballon-c1c7", "maduro-iran"):
        j = json.load(open(os.path.join(AUDIT, folder, "case_registry.json")))
        for c in (j if isinstance(j, list) else j.get("cases") or list(j.values())):
            if isinstance(c, dict) and c.get("case_id") not in SKIP and c.get("condition_ids"):
                yield c


def main(db, out):
    con = store.connect(db); res = []
    for c in cases():
        public, resolved = ts(c.get("first_public_information_utc")), ts(c.get("resolution_utc"))
        end = public or resolved
        flagged = {a.get("proxy", "").lower() for a in (c.get("flagged_accounts") or []) if isinstance(a, dict)}
        for cid in c["condition_ids"][:MAX_PER_CASE]:
            row = {"case_id": c["case_id"], "condition_id": cid, "end_is": "first_public_information" if public else "resolution", "end_utc": c.get("first_public_information_utc") or c.get("resolution_utc")}
            try:
                g = net.get_json(f"{collect.GAMMA}/markets?condition_ids={cid}&closed=true") or net.get_json(f"{collect.GAMMA}/markets?condition_ids={cid}")
                if not g:
                    row["status"] = "unknown_to_gamma"; res.append(row); continue
                m = collect.resolve(con, json.loads(g[0]["clobTokenIds"])[0])
                if m is None:
                    row["status"] = "not_a_yes_no_market"; res.append(row); continue
                t_end = end or m["end_ts"]
                if not t_end:
                    row["status"] = "no_end_time"; res.append(row); continue
                row.update(title=m["title"], tags=json.loads(m["tags"]), excluded_by_tag=bool(set(json.loads(m["tags"])) & collect.EXCLUDED_TAGS))
                for lo in range(t_end - WINDOW - 8 * 3600, t_end, 13 * 86400):
                    collect.fetch_prices(con, m["yes_token"], lo, min(t_end, lo + 13 * 86400))
                tape = collect.fetch_tape(con, m["condition_id"], t_end - WINDOW - 3600)
                row.update(tape_pages=tape["pages"], tape_rows=tape["rows"])
                if not tape["complete"]:
                    row["status"] = "tape_too_deep"; res.append(row); continue
                r = detect.backtest(con, m["condition_id"], t_end - WINDOW, t_end)
                row["status"] = "replayed"; row["sides"] = {}
                for side, x in r.items():
                    if x.get("level"):
                        row["sides"][side] = {"level": x["level"], "t_first_utc": x["t_first_utc"], "t_alert_utc": x["t_alert_utc"], "p_alert": x["p_alert"],
                                              "initiator": x["features"]["initiator"], "initiator_is_flagged_in_case": x["features"]["initiator"] in flagged,
                                              "share15": x["features"]["share15"], "prior_markets": x["initiator_history"]["prior_markets"],
                                              "hours_before_end": round((t_end - x["t_alert"]) / 3600, 2), "cluster_members": sum(len(s["new"]) for s in x["cluster_timeline"]),
                                              "other_groups": [{"as_of_utc": detect._utc(g["as_of"]), "wallets": g["wallets"], "shared_payer": g["shared_payer"]} for g in x["other_groups"]],
                                              "reasons": x["reasons"]}
                    else:
                        row["sides"][side] = {"level": None, "reason": x["reason"]}
            except net.SourceError as e:
                row["status"] = "source_error"; row["error"] = str(e)[:200]
            res.append(row)
            json.dump(res, open(out, "w"), indent=1)
            print(time.strftime("%H:%M:%S"), row["case_id"], cid[:12], row["status"], {s: (v.get("level") or v.get("reason")) for s, v in (row.get("sides") or {}).items()}, flush=True)
    print("done; requests:", dict(net.COUNTS))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
