"""Per-account table of the 38 names of post 2034030676589351244, from archived profiles and activity.

Reads data/g38_resolved_proxies.txt, data/ledger_g38.json (scripts/ledger.py), data_38_names.txt.
Writes data/g38_accounts.csv. The name comes from the public profile, else from the activity rows; ANON maps the
account without a public profile whose result matches the image's "Anon" line (REPORT.md section 4).
"""
import csv, glob, json, os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
ANON = {"0x8a480b60cb78213fdf34842160dc956a831a2558": "Anon"}
MILITARY = ["Iran", "Israel", "strike", "military", "Khamenei", "Hezbollah"]


def f(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%m-%d %H:%M") if t else ""


def main():
    L = json.loads((HERE / "data/ledger_g38.json").read_text())
    img = {l.split("\t")[0]: Decimal(l.split("\t")[1]) for l in (HERE / "data_38_names.txt").read_text().splitlines() if l.strip() and not l.startswith("#")}
    out = []
    for a in [l.strip() for l in (HERE / "data/g38_resolved_proxies.txt").read_text().splitlines() if l.strip()]:
        v = L[a]
        pp = RAW / "polymarket" / a / "profile.json"
        prof = json.loads(pp.read_text()) if pp.exists() else {}
        rows = []
        for p in sorted(glob.glob(str(RAW / "polymarket" / a / "v2activity_p*.json"))):
            if not p.endswith(".meta.json"):
                rows += json.loads(Path(p).read_text(), parse_float=Decimal)["data"]
        name = ANON.get(a) or prof.get("name") or ""
        iran = [r for r in rows if r["type"] == "TRADE" and "Iran" in (r["title"] or "")]
        fno = min((r["timestamp"] for r in iran if r["outcome"] == "No" and r["side"] == "BUY"), default=None)
        fyes = min((r["timestamp"] for r in iran if r["outcome"] == "Yes" and r["side"] == "BUY"), default=None)
        mk = sorted({r["title"] for r in rows if r["type"] == "TRADE"})
        wd = [r for r in rows if r["type"] == "WITHDRAWAL"]
        out.append({"name": name, "proxy": a, "profile_served": bool(prof), "created": (prof.get("createdAt") or "")[:16],
                    "first_activity": v["first_utc"][:16], "markets": len(mk),
                    "non_military_markets": sum(1 for m in mk if not any(k in m for k in MILITARY)),
                    "first_no": f(fno), "first_yes": f(fyes), "no_before_yes": bool(fno and fyes and fno < fyes),
                    "result": str(round(Decimal(v["trading_result"]), 2)), "image_pnl": str(img.get(name, "")),
                    "deposits": str(round(Decimal(v["totals"].get("deposits", "0")), 2)), "withdrawals": str(round(Decimal(v["totals"].get("withdrawals", "0")), 2)),
                    "n_withdrawals": len(wd), "first_withdrawal": f(min((r["timestamp"] for r in wd), default=None)), "open_tokens": len(v["open_share_tokens"])})
    out.sort(key=lambda r: r["created"] or r["first_activity"])
    with open(HERE / "data/g38_accounts.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    tot = sum(Decimal(r["result"]) for r in out)
    print(len(out), "accounts; result", tot, "; image", sum(img.values()), "; names matched", sum(1 for r in out if r["image_pnl"]))


if __name__ == "__main__":
    main()
