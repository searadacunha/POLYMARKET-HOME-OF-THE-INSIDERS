"""Write results/recovery_attempts.jsonl: one line per recovery attempt, read from the collectors' own logs and caches."""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path


def load(p, default=None):
    if not p.exists():
        return default
    return json.loads(gzip.decompress(p.read_bytes())) if p.suffix == ".gz" else json.loads(p.read_text())


def ledger_attempt(raw, name):
    ck = [json.loads(x) for x in (raw / name / "checkpoint.jsonl").read_text().splitlines() if x.strip()]
    run = (raw / name / "run.log").read_text().splitlines()
    plan = load(raw / name / "plan.json")
    return {"dataset": name, "source": plan["provider"], "method": "eth_getLogs, seven filters, adaptive ranges",
            "accounts": len(plan["accounts"]), "accepted_ranges": len(ck), "logs": sum(c["n"] for c in ck),
            "failed_stream_runs": sum("FAILED" in x for x in run),
            "outcome": "COMPLETE" if all("FAILED" not in x for x in run[-20:]) else "SEE run.log",
            "note": "a failed stream run stops without accepting the range and resumes from the checkpoint",
            "first_utc": ck[0]["received_utc"] if ck else "", "last_utc": ck[-1]["received_utc"] if ck else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    raw, out = a.raw, []
    for name in ("ledger", "ledger_pr111"):
        if (raw / name / "checkpoint.jsonl").exists():
            out.append(ledger_attempt(raw, name))
    for src in ("sources", "sources_pr111"):
        m = load(raw / src / "markets.json.gz", {})
        if m:
            out.append({"dataset": f"{src}/markets", "source": "gamma-api.polymarket.com/markets",
                        "method": "clob_token_ids batches of 40, closed then open, halved on HTTP 5xx",
                        "calls": len(m["calls"]), "tokens_known": len(m["tokens"]), "missing": len(m["missing"]),
                        "errors": len(m.get("errors", [])),
                        "outcome": "COMPLETE" if not m.get("errors") else "PARTIAL"})
        r = load(raw / src / "resolutions.json.gz", {})
        if r:
            out.append({"dataset": f"{src}/resolutions", "source": "Conditional Tokens ConditionResolution logs",
                        "method": "topic-1 OR-lists of 100 conditions", "conditions_queried": len(r["queried"]),
                        "resolved": len(r["conditions"]), "ranges": len(r["ranges"]), "outcome": "COMPLETE"})
        b = load(raw / src / "balances.json.gz", {})
        if b:
            out.append({"dataset": f"{src}/balances", "source": "eth_call balanceOf (archive)",
                        "collateral_reads": len(b.get("collateral", {})), "position_reads": len(b.get("positions", {})),
                        "outcome": "COMPLETE"})
        act = load(raw / src / "activity.json.gz", {})
        if act:
            st = Counter(v["status"] for v in act["accounts"].values())
            out.append({"dataset": f"{src}/activity", "source": "data-api.polymarket.com/v2/activity",
                        "accounts": len(act["accounts"]), "pages": sum(len(v["pages"]) for v in act["accounts"].values()),
                        "rows": sum(len(v["rows"]) for v in act["accounts"].values()), "status": dict(st),
                        "outcome": "COMPLETE" if set(st) == {"EXHAUSTED"} else "PARTIAL"})
        mk = load(raw / src / "marks.json.gz", {})
        if mk:
            out.append({"dataset": f"{src}/marks", "source": "clob.polymarket.com/prices-history",
                        "method": "last point at or before the valuation time, one-day window",
                        "tokens": len(mk["tokens"]),
                        "with_point": sum(1 for v in mk["tokens"].values() if v["price"] is not None),
                        "outcome": "PARTIAL" if any(v["price"] is None for v in mk["tokens"].values()) else "COMPLETE"})
    rs = load(a.results / "relay_v2_screen.json", {})
    if rs:
        out.append({"dataset": "relay_v2", "source": "api.relay.link/requests/v2", "accounts": rs["accounts"],
                    "http_calls": rs["http_calls"], "http_429": rs["http_429"], "status": rs["status_now"],
                    "outcome": "COMPLETE" if rs["status_now"].get("EXHAUSTED") == rs["accounts"] else "PARTIAL",
                    "note": "endpoint retired 2026-11-24T00:00:00Z; v3 requires an API key, not obtained"})
    eth = (a.results / "eth_weeks_coverage.csv").read_text().splitlines()[1:]
    out.append({"dataset": "eth_weeks", "source": "PR 110 collect_week (pinned) on public Ethereum RPC; keyless explorer",
                "rows": len(eth), "outcome": "PARTIAL",
                "note": "log streams complete; native stream partial: explorer HTTP 429, Etherscan needs a key"})
    out.append({"dataset": "audit_candidate_zip", "source": "local search (Spotlight, Downloads, Desktop)",
                "outcome": "UNAVAILABLE", "note": "the mission's audit_data_coverage ZIP was not found on this Mac; "
                                                  "an original audit script was written instead"})
    for name, why in (("polymarket_subgraphs", "HTTP 429 paused and deprecated"), ("goldsky_edge", "HTTP 402 payment"),
                      ("envio_hypersync", "HTTP 401 token"), ("relay_requests_v3", "x-api-key required"),
                      ("clob_historical_book", "no endpoint; /book 404 after close"),
                      ("publicnode_archive", "HTTP 403 beyond about 2-3M blocks")):
        out.append({"dataset": name, "source": "public endpoint probe", "outcome": "UNAVAILABLE", "note": why})
    (a.results / "recovery_attempts.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in out))
    print(len(out), "attempts")


if __name__ == "__main__":
    main()
