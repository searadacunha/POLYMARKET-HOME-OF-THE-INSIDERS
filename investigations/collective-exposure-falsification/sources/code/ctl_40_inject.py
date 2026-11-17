#!/usr/bin/env python3
"""Positive and negative controls: synthetic collective shifts injected into real TRAIN tapes (TRAIN only).

For a hash-chosen 25 % of TRAIN markets (sha256(scenario|seed|cid) mod 4 == 0), 3 wallets each buy 1,500 shares of
side s* at the last executed price of s*, at t0 + 60 s, + 300 s, + 600 s, where t0 is a hash-chosen grid time with
p(s*) in [0.2, 0.7] between first fill + 2 h and last fill - 1 h. Each buy is minted against one synthetic
counterparty buying the other side at 1 - p in the same transaction (balanced, as in mission 4's own control).

Scenarios (P(s* = winner)):
  STRONG 1.00, MEDIUM 0.75, WEAK 0.60, NULL 0.50 (random side: negative control) - fresh synthetic wallets;
  OLD    0.75 with 3 REAL TRAIN wallets first seen >= 30 days before t0 and absent from the market (so F4 'young'
         cannot give the injection away);
  FUNDLINK 0.50 (collective shift carries no information) but, only when s* is the winner, the 3 fresh wallets
         share a common non-hub funder and wallets 0 and 1 have a direct USDC transfer 2 days before t0: a positive
         control for M4 (T5) that M3 cannot see.
Labels of TRAIN markets are read here (TRAIN only); a winner other than YES/NO is refused.
Outputs: inject.json {cid: [rows]}, inject_manifest.json, and for FUNDLINK inject_funding.json.

usage: ctl_40_inject.py --tapes T.sqlite [...] --markets ROLE=PATH [...] --labels labels.jsonl.gz
                        --scenario STRONG --seed 1 --out inject.json [--wallet-first controles/wallet_first.json]
"""
import argparse
import bisect
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feat_30_detect as F  # noqa: E402

PROB = {"STRONG": 1.00, "MEDIUM": 0.75, "WEAK": 0.60, "NULL": 0.50, "OLD": 0.75, "FUNDLINK": 0.50}
SHARES = 1500.0
G = 900
OLD_DAYS = 30


def h(*p):
    return int(hashlib.sha256("|".join(str(x) for x in p).encode()).hexdigest()[:12], 16)


def wallet_first_seen(cons, path):
    """First fill of every wallet over the TRAIN tapes, cached (one sequential scan per database)."""
    if path and os.path.exists(path):
        return json.load(open(path))
    first = {}
    for con in cons:
        for w, ts in con.execute("select wallet, min(ts) from trades group by wallet"):
            w = (w or "").lower()
            if w and (w not in first or ts < first[w]):
                first[w] = ts
    if path:
        json.dump(first, open(path, "w"))
    return first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--markets", action="append", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--scenario", choices=sorted(PROB), required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wallet-first")
    a = ap.parse_args()
    markets = F.load_markets(a.markets)
    train = {c for c, m in markets.items() if m["role"] == "TRAIN"}
    chosen = sorted(c for c in train if h(a.scenario, a.seed, c) % 4 == 0)
    lab = {}
    with gzip.open(a.labels, "rt") as f:
        for l in f:
            r = json.loads(l)
            c = r["condition_id"].lower()
            if c in train:   # TRAIN labels only
                if r["winner"] not in ("YES", "NO"):
                    raise SystemExit(f"unexpected winner {r['winner']!r} for {c}: refused")
                lab[c] = r["winner"]
    cons = [F.open_ro(t) for t in a.tapes]
    wfirst = wallet_first_seen(cons, a.wallet_first) if a.scenario == "OLD" else {}
    old_pool = sorted(wfirst) if wfirst else []
    out, fund_extra = {}, {"direct": {}, "funders": {}, "status": {}}
    man = {"scenario": a.scenario, "seed": a.seed, "chosen": len(chosen), "injected": 0, "no_tape": 0,
           "no_time": 0, "no_old_wallets": 0, "s_is_winner": 0, "injected_wallets": {}}
    rid = 10 ** 12
    for c in chosen:
        rows = None
        for con in cons:
            rows = con.execute("select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, "
                               "tx, token_id from trades where condition_id=? order by ts, rowid", (c,)).fetchall()
            if rows:
                break
        if not rows or c not in lab:
            man["no_tape"] += 1
            continue
        win = 0 if lab[c] == "YES" else 1
        s = win if (h(a.scenario, a.seed, c, "side") % 10000) / 10000.0 < PROB[a.scenario] else 1 - win
        ts_s = [r[2] for r in rows if int(r[6]) == s]
        px_s = [r[8] for r in rows if int(r[6]) == s]
        lo, hi = rows[0][2] + 7200, rows[-1][2] - 3600
        ok = []
        for t in (g * G for g in range(-(-lo // G), hi // G + 1)):
            i = bisect.bisect_right(ts_s, t) - 1
            if i >= 0 and 0.2 <= px_s[i] <= 0.7:
                ok.append((t, px_s[i]))
        if not ok:
            man["no_time"] += 1
            continue
        t0, p = ok[h(a.scenario, a.seed, c, "t") % len(ok)]
        if a.scenario == "OLD":
            here = {(r[3] or "").lower() for r in rows}
            elig = [w for w in old_pool if wfirst[w] < t0 - OLD_DAYS * 86400 and w not in here]
            if len(elig) < 3:
                man["no_old_wallets"] += 1
                continue
            start = h(a.scenario, a.seed, c, "w") % len(elig)
            wallets = [elig[(start + 7919 * k) % len(elig)] for k in range(3)]
            if len(set(wallets)) < 3:
                man["no_old_wallets"] += 1
                continue
        else:
            wallets = ["0x" + hashlib.sha256(f"syn|{a.scenario}|{a.seed}|{c}|{k}".encode()).hexdigest()[:40]
                       for k in range(3)]
        cid_raw = rows[0][1]
        tok = {int(r[6]): r[10] for r in rows}
        oc = {int(r[6]): r[5] for r in rows}
        cpty = "0x" + hashlib.sha256(f"cpty|{a.scenario}|{a.seed}|{c}".encode()).hexdigest()[:40]
        inj = []
        for k, dt_ in enumerate((60, 300, 600)):
            tx = "0xsyn" + hashlib.sha256(f"tx|{a.scenario}|{a.seed}|{c}|{k}".encode()).hexdigest()[:60]
            inj.append([rid, cid_raw, t0 + dt_, wallets[k], "BUY", oc.get(s, "Yes" if s == 0 else "No"), s, SHARES,
                        p, tx, tok.get(s, "")])
            inj.append([rid + 1, cid_raw, t0 + dt_, cpty, "BUY", oc.get(1 - s, "No" if s == 0 else "Yes"), 1 - s,
                        SHARES, round(1 - p, 6), tx, tok.get(1 - s, "")])
            rid += 2
        if a.scenario == "FUNDLINK":
            for w in wallets:
                fund_extra["status"][w] = "complete"
            if s == win:
                funder = "0x" + hashlib.sha256(f"funder|{a.seed}|{c}".encode()).hexdigest()[:40]
                for w in wallets:
                    fund_extra["funders"][w] = {funder: t0 - 3 * 86400}
                fund_extra["direct"]["|".join(sorted(wallets[:2]))] = [t0 - 2 * 86400]
        out[c] = inj
        man["injected"] += 1
        man["s_is_winner"] += int(s == win)
        man["injected_wallets"][c] = {"wallets": wallets, "t0": t0, "side": "YES" if s == 0 else "NO",
                                      "is_winner": s == win}
    json.dump(out, open(a.out, "w"))
    man["out_sha256"] = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    if a.scenario == "FUNDLINK":
        json.dump(fund_extra, open(a.out.replace(".json", "_funding.json"), "w"))
    json.dump(man, open(a.out.replace(".json", "_manifest.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in man.items() if k != "injected_wallets"}))


if __name__ == "__main__":
    main()
