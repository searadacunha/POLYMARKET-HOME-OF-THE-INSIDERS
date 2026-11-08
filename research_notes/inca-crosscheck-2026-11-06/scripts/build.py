"""Applies PLAN_CONTROLS.md to the analysed set S (controls + five Inca accounts).

  python3 -I scripts/build.py needs     list the recipients to classify (labels and eth_getCode)
  python3 -I scripts/build.py results   write data/flows.csv, data/relay_orders.csv, data/results.json
"""
import csv, json, math, re, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
sys.path.insert(0, str(HERE))
from rules import withdrawal_recipients, deposit_funders, links  # noqa: E402
from collect import RAW  # noqa: E402

POP = json.loads((NOTE / "data" / "population.json").read_text())
INCA = {"0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a": "9TungSahur", "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a": "PorcoRosso",
        "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": "ricosuave666", "0xcb18ea2923d957bd9cf049cce60a87638722f867": "DonkeyDonkey999",
        "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44": "truthlord"}
INCA3 = ["0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a", "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2", "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44"]
INCA2 = ["0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a", "0xcb18ea2923d957bd9cf049cce60a87638722f867"]
S = sorted(set(POP["controls"]) | set(INCA))
_plan = (NOTE / "PLAN_CONTROLS.md").read_text().split("## N27")[1].split("## Comparison")[0]
NET = [r["address"] for r in csv.DictReader(open(NOTE.parent / "iran-cluster-e-network-2026-11-05" / "accounts.csv"))
       if r["group"] == "cluster E network"]
N27 = {x.lower() for x in re.findall(r"0x[0-9a-fA-F]{40}", _plan)} | set(re.findall(r"`([1-9A-HJ-NP-Za-km-z]{32,44})`", _plan)) | set(NET)
CHECKED = []
KNOWN_CONTRACTS = {"0xd36ec33c8bed5a9f7b6630855f1533455b98a418", "0xd216153c06e857cd7f72665e0af1d7d82172f494"}


def _pages(d, pat):
    if not (d / "DONE.json").exists():
        return None
    rows = []
    for p in sorted(d.glob(pat)):
        if not p.name.endswith(".meta.json"):
            rows += json.loads(p.read_text())["data"]
    return rows


def activity(w):
    """DEPOSIT and WITHDRAWAL rows (amendment A1); equal to the full activity wherever both were read."""
    dw = _pages(RAW / "polymarket_dw" / w, "p*.json")
    if dw is None:
        raise SystemExit(f"{w}: deposits and withdrawals incomplete")
    full = _pages(RAW / "polymarket" / w, "v2activity_p*.json")
    if full is not None:
        key = lambda r: (r["transaction_hash"], r["type"], r["usdc_size"])
        a = sorted(map(key, dw)); b = sorted(key(r) for r in full if r["type"] in ("DEPOSIT", "WITHDRAWAL"))
        if a != b:
            raise SystemExit(f"{w}: filtered rows differ from the full activity")
        CHECKED.append(w)
    return dw


def relay(w):
    d = RAW / "relay" / w
    if not (d / "DONE.json").exists():
        raise SystemExit(f"{w}: Relay incomplete")
    out = []
    for p in sorted(d.glob("p*.json")):
        if not p.name.endswith(".meta.json"):
            out += json.loads(p.read_text())["requests"]
    return out


def receipt(h):
    p = RAW / "polygon" / f"{h.lower()}.eth_getTransactionReceipt.json"
    if not p.exists():
        raise SystemExit(f"{h}: receipt missing")
    return json.loads(p.read_text())["result"]


def flows():
    rows, rel, unresolved = [], [], defaultdict(int)
    for w in S:
        for r in activity(w):
            if r["type"] not in ("DEPOSIT", "WITHDRAWAL"):
                continue
            rc = receipt(r["transaction_hash"])
            cps = deposit_funders(rc, w) if r["type"] == "DEPOSIT" else withdrawal_recipients(rc, w)
            if not cps:
                unresolved[w] += 1
            for cp, amt, tok in cps or [("", 0.0, "")]:
                rows.append({"wallet": w, "type": r["type"], "ts": int(r["timestamp"]), "usdc": float(r["usdc_size"]),
                             "hash": r["transaction_hash"].lower(), "counterparty": cp, "cp_amount": amt, "cp_token": tok})
        for q in relay(w):
            u, rcp = (q.get("user") or "").lower(), (q.get("recipient") or "")
            rcp_l = rcp.lower() if rcp.startswith("0x") else rcp
            if u == w and rcp_l != w:
                rel.append({"wallet": w, "dir": "out", "other": rcp_l, "id": q["id"], "status": q["status"], "created": q["createdAt"]})
            elif rcp_l == w and u != w:
                rel.append({"wallet": w, "dir": "in", "other": u if u.startswith("0x") else q.get("user"), "id": q["id"],
                            "status": q["status"], "created": q["createdAt"]})
    return rows, rel, unresolved


def recipients(rows, rel):
    out = defaultdict(set)
    for r in rows:
        if r["type"] == "WITHDRAWAL" and r["counterparty"]:
            out[r["counterparty"]].add(r["wallet"])
    for r in rel:
        if r["dir"] == "out" and r["status"] == "success":
            out[r["other"]].add(r["wallet"])
    return out


def service_set(addrs):
    svc, unchecked = set(KNOWN_CONTRACTS), []
    tagged = set()
    for p in (RAW / "blockscout").glob("rcpt_S_137_*.json"):
        if not p.name.endswith(".meta.json"):
            for k, v in (json.loads(p.read_text()).get("addresses") or {}).items():
                if v.get("tags"):
                    tagged.add(k.lower())
    for a in addrs:
        if not a.startswith("0x"):
            continue
        c = RAW / "polygon_code" / f"{a}.json"
        if not c.exists():
            unchecked.append(a); continue
        if json.loads(c.read_text())["result"] not in ("0x", "0x0"):
            svc.add(a)
        if a in tagged:
            svc.add(a)
    return svc, unchecked


def wilson(k, n):
    if n == 0:
        return [None, None]
    z, p = 1.959964, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 4), round(c + h, 4)]


def fisher_greater(a, n1, b, n2):
    """One-sided P(X >= a), X ~ hypergeometric with a + b successes among n1 + n2, n1 drawn."""
    K, N = a + b, n1 + n2
    tot = math.comb(N, n1)
    return sum(math.comb(K, x) * math.comb(N - K, n1 - x) for x in range(a, min(K, n1) + 1)) / tot


def main(mode):
    rows, rel, unresolved = flows()
    rec = recipients(rows, rel)
    if mode == "needs":
        print(" ".join(sorted(a for a in rec if a.startswith("0x"))))
        return
    svc, unchecked = service_set(rec)
    if unchecked:
        raise SystemExit(f"{len(unchecked)} recipients without eth_getCode: collect them first")
    # M1: funder or recipient in N27 (Polygon flows and Relay)
    m1 = defaultdict(list)
    for r in rows:
        if r["counterparty"] in N27:
            m1[r["wallet"]].append(("polygon", r["type"], r["counterparty"], r["hash"]))
    for r in rel:
        if r["other"] in N27 and r["status"] == "success":
            m1[r["wallet"]].append(("relay", r["dir"], r["other"], r["id"]))
    # M2: non-service recipient shared with another wallet of S
    m2 = defaultdict(set)
    for a, ws in rec.items():
        if a not in svc and len(ws) > 1:
            for w in ws:
                m2[w] |= {(a, x) for x in ws if x != w}
    # M3: direct same hash, or two or more matched legs
    legs = [{"wallet": r["wallet"], "type": r["type"], "ts": r["ts"], "usdc": r["usdc"], "hash": r["hash"]}
            for r in {(r["wallet"], r["hash"]): r for r in rows}.values()]
    direct, matched = links(legs)
    m3 = defaultdict(set)
    for a, b in direct:
        m3[a["wallet"]].add(("direct", b["wallet"], a["hash"])); m3[b["wallet"]].add(("direct", a["wallet"], a["hash"]))
    for (a, b), v in matched.items():
        m3[a].add(("matched", b, len(v))); m3[b].add(("matched", a, len(v)))
    ctrl = POP["controls"]
    res = {"controls": len(ctrl), "analysed": len(S), "unresolved_rows": dict(unresolved),
           "unresolved_controls": sum(1 for w in ctrl if unresolved.get(w)), "services_excluded": len(svc), "a1_equality_checked": len(set(CHECKED)), "measures": {}}
    for name, m in (("M1", m1), ("M2", m2), ("M3", m3)):
        kc = sum(1 for w in ctrl if m.get(w)); k3 = sum(1 for w in INCA3 if m.get(w)); k2 = sum(1 for w in INCA2 if m.get(w))
        res["measures"][name] = {"controls": [kc, len(ctrl), wilson(kc, len(ctrl))], "inca3": [k3, 3, wilson(k3, 3)],
                                 "inca2": [k2, 2], "p_one_sided_inca3_vs_controls": fisher_greater(k3, 3, kc, len(ctrl)),
                                 "who": {w: sorted(map(list, m[w])) for w in S if m.get(w)}}
    ps = sorted((res["measures"][k]["p_one_sided_inca3_vs_controls"], k) for k in res["measures"])
    for i, (p, k) in enumerate(ps):  # Holm step-down, monotone
        res["measures"][k]["p_holm"] = min(1.0, max((len(ps) - j) * ps[j][0] for j in range(i + 1)))
    (NOTE / "data").mkdir(exist_ok=True)
    with open(NOTE / "data" / "flows.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(sorted(rows, key=lambda r: (r["wallet"], r["ts"])))
    with open(NOTE / "data" / "relay_orders.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rel[0])); wr.writeheader(); wr.writerows(sorted(rel, key=lambda r: (r["wallet"], r["created"])))
    (NOTE / "data" / "results.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps({k: {x: v[x] for x in ("controls", "inca3", "inca2", "p_one_sided_inca3_vs_controls", "p_holm")}
                      for k, v in res["measures"].items()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
