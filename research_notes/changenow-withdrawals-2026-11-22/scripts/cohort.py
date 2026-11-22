"""Forward check from known Polymarket wallets: every collateral transfer out of each wallet over its whole life, and
whether the recipient handed the money to a registered ChangeNOW payout wallet soon after. Network collector.

It answers two questions the week-by-week census cannot: withdrawals outside the weeks read (before 2026-04-13, or
after the last closed week), and withdrawals the census missed inside them (a check of its completeness).
A recipient counts as a ChangeNOW deposit address when, within a day of receiving the wallet's money, it paid a
registered payout wallet (tier A or B) and it is a plain key that signed at most two transactions in its life
(the census rule for single-use deposit addresses). The wallet's own key is followed one hop further the same way.
Lists come from Etherscan v2 (chain 137) with the same complete-paging rule as the census; nothing is inferred
from an amount or a time alone.

Wallets: the census results (established and possible), and the 153 trading accounts paid by 0xf2020cbf... between
2026-04-14 and 2026-06-22 (investigations/changenow-polymarket/sources/state/pm_traders.csv).
"""
import argparse
import csv
import gzip
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "monitoring"))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from changenow_weekly import chainio as io, prices, registry  # noqa: E402
from changenow_weekly import polymarket as pm  # noqa: E402
import census  # noqa: E402  measured endpoint lists, batch sizes and the nonce cache

COLLATERAL = {pm.USDC_E, pm.USDC, pm.PUSD}
DAY = 86400


def tokentx(address, cache, keep, name):
    """ERC-20 transfers of one Polygon address from Etherscan (complete paging), ascending. Only the rows `keep`
    accepts are cached on disk, with the count of rows read: a trading wallet's list holds every trade."""
    path = cache / name / f"{address}.json.gz"
    if path.exists():
        with gzip.open(path, "rt") as f:
            return json.load(f)["rows"]
    rows = io.etherscan_rows(137, "tokentx", address, 0, 99_999_999)
    out = [dict(block=int(r["blockNumber"]), ts=int(r["timeStamp"]), tx=r["hash"].lower(), src=r["from"].lower(), dst=r["to"].lower(),
                token=r["contractAddress"].lower(), raw=int(r["value"]), log_index=int(r.get("logIndex") or -1)) for r in rows]
    out = [r for r in out if keep(r)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as f:
        json.dump(dict(read=len(rows), rows=out), f, separators=(",", ":"))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--env-file")
    p.add_argument("--outflows", default=str(HERE.parent / "results" / "changenow_outflows.csv"))
    p.add_argument("--max-wallets", type=int, default=2000)
    args = p.parse_args(argv)
    census.load_key(args.env_file)
    reg = registry.load()
    sinks = set(registry.usable(reg))
    raw = Path(args.raw)
    cache = raw / "cohort" / "tokentx"
    wallets = {}
    if Path(args.outflows).exists():
        with open(args.outflows, newline="") as f:
            for r in csv.DictReader(f):
                for w in r["polymarket_wallet"].split("|"):
                    if len(w) == 42 and r["evidence_class"] != "UNRESOLVED":
                        wallets.setdefault(w, "census")
    with open(REPO / "investigations/changenow-polymarket/sources/state/pm_traders.csv", newline="") as f:
        for r in csv.DictReader(f):
            wallets.setdefault(r["account"].lower(), "f2020_funded_cohort")
    wallets = dict(sorted(wallets.items())[: args.max_wallets])
    found, owners, checked = [], {}, 0
    io.CHAINS[137]["state"] = list(census.POLYGON_STATE)
    (raw / "cohort").mkdir(parents=True, exist_ok=True)
    book = prices.Book(raw / "cohort" / "prices.json")
    for w, origin in wallets.items():
        try:
            outs = tokentx(w, cache, lambda r, w=w: r["src"] == w and r["token"] in COLLATERAL and r["raw"] > 0, "wallets")
        except Exception as exc:                                    # one wallet that no list serves is reported, never read as empty
            found.append(dict(wallet=w, origin=origin, error=str(exc)[:160]))
            continue
        c = pm.classify(w) if outs else {}
        owner_keys = [o.lower() for o in (c.get("owners") or [])]
        owners[w] = owner_keys
        for r in outs:
            hops = [(r, r["dst"])]
            if r["dst"] in owner_keys:                              # the wallet paid its own key: follow the key one hop
                key_rows = [x for x in tokentx(r["dst"], cache, lambda x, k=r["dst"]: x["src"] == k and x["raw"] > 0, "keys") if r["ts"] <= x["ts"] <= r["ts"] + 3 * DAY]
                hops = [(x, x["dst"]) for x in key_rows]
            for leg, recipient in hops:
                if recipient in sinks:
                    found.append(dict(wallet=w, origin=origin, kind="PAID_A_REGISTERED_WALLET", debit=r, leg=leg, recipient=recipient))
                    continue
                if recipient in COLLATERAL or pm.ff_flows.label_of(recipient) or recipient == io.ZERO:
                    continue
                sweep = [x for x in tokentx(recipient, cache, lambda x, a=recipient: x["src"] == a and x["dst"] in sinks, "recipients") if leg["ts"] <= x["ts"] <= leg["ts"] + DAY]
                checked += 1
                if not sweep:
                    continue
                nonce = census.cached_nonces(137, [recipient])[recipient]
                hit = dict(wallet=w, origin=origin, kind="DEPOSIT_ADDRESS" if 1 <= nonce <= 2 else "PAID_A_SENDER_OF_THE_SERVICE",
                           debit=r, leg=leg, recipient=recipient, recipient_nonce=nonce, sweep=sweep[0], sink=sweep[0]["dst"],
                           sink_tier=reg[sweep[0]["dst"]]["tier"], via_key=leg is not r)
                if hit["kind"] == "DEPOSIT_ADDRESS":
                    info = book.recognise(137, [leg["token"]]).get(leg["token"])
                    if info:
                        try:
                            price, price_ts = book.at(137, leg["token"], leg["ts"])
                            amount = leg["raw"] / 10 ** info["decimals"]
                            hit["value"] = dict(symbol=pm.COLLATERAL.get(leg["token"], (info["symbol"],))[0], decimals=info["decimals"], amount=amount,
                                                price_usd=price, price_ts=price_ts, usd=round(amount * price, 2))
                        except pm.net.SourceError as exc:
                            hit["value"] = dict(error=str(exc)[:160])
                found.append(hit)
        time.sleep(0.05)
    out = dict(generated_ts=int(time.time()), wallets=len(wallets), origins=dict(sorted({o: sum(1 for v in wallets.values() if v == o) for o in set(wallets.values())}.items())),
               recipients_checked=checked, owners=owners, found=found)
    book.save()
    (raw / "cohort" / "forward.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"{len(wallets)} wallets, {checked} recipients checked, {sum(1 for f in found if f.get('kind') == 'DEPOSIT_ADDRESS')} deposit-address hits, "
          f"{sum(1 for f in found if 'error' in f)} errors", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
