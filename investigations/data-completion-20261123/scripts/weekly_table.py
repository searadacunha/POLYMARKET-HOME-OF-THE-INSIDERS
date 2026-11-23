"""Weekly service-funding table in the mission's columns, derived from PR #110's pinned outputs plus this session's
Ethereum stream recovery and Relay v2 screen. Nothing of PR #110 is recomputed or changed: its frozen sets and series
are read from Git objects at 8b633048 and only reshaped.

One row per ISO week (UTC) x service x evidence level. Distinct wallets come from PR #110's per-week address sets;
the all-period row is a set union, never a sum of weekly counts. The platform-wide denominator stays UNKNOWN.
"""

import argparse
import csv
import io
import json
import subprocess
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

PR110 = "8b633048290e7174945bc811b16cf0b11b4d8ceb"
BASE = "investigations/weekly-funding-intelligence/"
LEVEL_SET = {"CONFIRMED_DIRECT": "direct", "SUPPORTED_INDIRECT": "indirect", "POSSIBLE": "possible"}
SERVICES = {"ChangeNOW": "changenow", "Tornado Cash": "tornado"}
FIELDS = ["week", "service", "evidence_level", "verified_distinct_wallets", "possible_distinct_wallets",
          "unique_transactions", "value_by_token", "usd_valuation", "active_sample_size", "sample_membership",
          "traded_after_funding", "coverage_status", "uncensored_source_count", "source_gap_count",
          "unknown_universe", "ethereum_stream_recovery", "source"]


def git(repo, path):
    return subprocess.run(["git", "-C", str(repo), "show", f"{PR110}:{BASE}{path}"], check=True,
                          capture_output=True).stdout


def build(repo, eth_csv):
    w = json.loads(git(repo, "results/weekly_funding.json"))
    funding = list(csv.DictReader(io.StringIO(git(repo, "results/wallet_funding.csv").decode())))
    eth = defaultdict(dict)
    if eth_csv and Path(eth_csv).exists():
        for r in csv.DictReader(open(eth_csv)):
            eth[r["week"]][r["stream"]] = r
    rows, union = [], defaultdict(lambda: defaultdict(set))
    for week in sorted(w["sets"]):
        cov = w["coverage"][week]
        for service, key in SERVICES.items():
            streams = {s: v for s, v in cov.items() if s.endswith("/" + key) or s.startswith("1/" + key)}
            ok = [s for s, v in streams.items() if v["status"] in ("SCOPED_COMPLETE", "COMPLETE")]
            gaps = [s for s in streams if s not in ok]
            status = "; ".join(f"{s}:{v['status']}" for s, v in sorted(streams.items()))
            ser = w["series"][week].get(service, {})
            sets = w["sets"][week].get(service, {})
            er = eth.get(week, {})
            rec = "; ".join(f"{s}:{r['coverage_status']} events={r['events']} recipients={r['distinct_recipients']}"
                            for s, r in sorted(er.items()) if s.startswith("1/" + key)) or "not in recovery scope"
            for level, set_key in LEVEL_SET.items():
                members = set(sets.get(set_key) or [])
                union[service][level] |= members
                fr = [r for r in funding if r["week"] == week and r["service"] == service and r["evidence"] == level]
                by_token = defaultdict(Decimal)
                for r in fr:
                    by_token[r["token"]] += Decimal(r["amount"])
                usd = sum((Decimal(r["usd_known"]) for r in fr if r["usd_known"] not in ("", "UNKNOWN")), Decimal(0))
                rows.append({
                    "week": week, "service": service, "evidence_level": level,
                    "verified_distinct_wallets": len(members) if level != "POSSIBLE" else 0,
                    "possible_distinct_wallets": len(members) if level == "POSSIBLE" else 0,
                    "unique_transactions": len({(r["chain"], r["tx"]) for r in fr}),
                    "value_by_token": json.dumps({k: str(v) for k, v in sorted(by_token.items())}),
                    "usd_valuation": str(usd.quantize(Decimal("0.01"))),
                    "active_sample_size": ser.get("covered_active_pm", "UNKNOWN"),
                    "sample_membership": f"pm_sample:{cov.get('pm_sample', {}).get('status', 'UNKNOWN')} "
                                         f"ranges={len(cov.get('pm_sample', {}).get('ranges', []))}",
                    "traded_after_funding": len({r["wallet"] for r in fr if r.get("traded_after") == "YES"}),
                    "coverage_status": status,
                    "uncensored_source_count": len(ok), "source_gap_count": len(gaps),
                    "unknown_universe": ser.get("platform_denominator", "UNKNOWN"),
                    "ethereum_stream_recovery": rec,
                    "source": f"{PR110[:12]}:{BASE}results/weekly_funding.json (sets, series, coverage) and "
                              f"results/wallet_funding.csv",
                })
    all_period = {s: {lvl: len(v) for lvl, v in d.items()} for s, d in union.items()}
    return rows, all_period


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--eth-csv", type=Path)
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    rows, union = build(a.repo, a.eth_csv)
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    wr.writeheader()
    wr.writerows(rows)
    (a.results / "weekly_service_funding.csv").write_text(buf.getvalue())
    out = {"weeks": len({r["week"] for r in rows}), "rows": len(rows),
           "all_period_distinct_wallets_set_union": union,
           "note": "all-period counts are unions of PR #110's weekly address sets; never sums of weekly counts"}
    (a.results / "weekly_service_funding_union.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
