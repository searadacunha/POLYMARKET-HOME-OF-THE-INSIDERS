#!/usr/bin/env python3
"""Offline evaluation of the exchange-deposit-address test of tornado_demix (commit cc30ba7).

Own re-implementation from a reading of tornado_demix/deposit_addresses.py; the third-party
code is neither imported nor run. Reads only archived Etherscan v2 pages, Blockscout labels
and BSC nonce reads of two research notes. No network.

    python3 -I -B demixer_eval.py <cluster-e note dir> <previous note dir>
"""
import json
import sys
from collections import Counter
from pathlib import Path

# Thresholds as read in deposit_addresses.py:33-41
MAX_TXS, MAX_SENDERS, MIN_SHARE, TOP = 1000, 50, 0.8, 3
HOT_TXS, FWD_BLOCKS, FWD_NATIVE, FWD_TOKEN = 10000, 3200, 10**16, 0.01

USDC, USDCE = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
STABLE = {USDC, USDCE, "0xc2132d05d31c914a87c6611c10748aeb04b58e8f", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}
# Contracts known from the archived labels (Relay Depository, Relay router, Uniswap pool) and the tokens.
CONTRACTS = STABLE | {"0x4cd00e387622c35bddb9b4c962c136462338bc31", "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222",
                      "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"}
EIP7702 = {"0xa6c221448af73af8350291c5cdcd877b39683766"}  # type-4 tx archived in evidence/polygon
BRANDS = ("Binance", "Bybit", "Crypto.com", "Coinbase", "OKX", "Kraken", "KuCoin")

# Report classification (REPORT.md lines given in the evaluation report)
CASES = {
    "0x519fa16e9897132b7633f634b76306a327839e06": ("exchange deposit", "Binance customer deposit address", "prev"),
    "0x9063493a4233006be654da772ef4dc38720cac55": ("exchange deposit", "Crypto.com customer deposit address", "this"),
    "0x93b7e169b93ece646d08cedbb8fa505796a5b96b": ("exchange deposit", "Bybit customer deposit address", "this"),
    "0xa6c221448af73af8350291c5cdcd877b39683766": ("other per-customer", "EIP-7702 customer-specific wallet", "prev"),
    "0x98d4e9aa9527316598c4ee6783329b529e292bcb": ("other per-customer", "receiving account's own deposit address", "this"),
    "0xed412759234979acf5818121bc37c606373262b2": ("other per-customer", "receiving account's own deposit address", "this"),
    "0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978": ("other per-customer", "intermediary of rrrrgggbbbclat (alias)", "this"),
    "0x0b0d7e72412b099b472b8a339b95da9e87bd16e8": ("unlabeled", "pair H shared recipient, unlabeled", "this"),
    "0xc5bb1be0407db7312911ec765d399d02461e411a": ("unlabeled", "group G recipient, unlabeled, mainly to Coinbase 16", "this"),
}


def low(a):
    return (a or "").lower()


def load_pages(dirs, addr):
    got = {}
    for kind in ("txlist", "tokentx"):
        for d in dirs:
            p = d / "evidence" / "etherscan" / f"137_{kind}_{addr}_p1.json"
            if p.exists():
                got[kind] = json.loads(p.read_text())["result"]
                break
    return got.get("txlist"), got.get("tokentx", [])


def load_tags(dirs):
    tags = {}
    for d in dirs:
        for p in (d / "evidence" / "http").glob("bs_meta_137_*.json"):
            if p.name.endswith(".meta.json"):
                continue
            for a, v in (json.loads(p.read_text()).get("addresses") or {}).items():
                tags.setdefault(low(a), [(t.get("name") or "", t.get("tagType")) for t in v.get("tags", [])])
    return tags


def exchange(tags, a):
    """Stand-in for the demixer's category == 'exchange' (its attribution CSV is not available offline)."""
    names = [n for n, _ in tags.get(a, [])]
    if not any(n in ("Exchange", "HOT WALLET") or n.startswith(BRANDS) for n in names):
        return None
    brand = next((b for n in names for b in BRANDS if n.startswith(b)), None)
    return brand or next((n.split()[0] for n, t in tags.get(a, []) if t == "name"), "exchange")


def asset(r):
    return low(r.get("contractAddress")) or "native"


def forwards(rows, addr, target):
    """deposit_addresses.py:70-101: target got an amount addr had just received (same asset)."""
    inc = [r for r in rows if low(r["to"]) == addr and str(r.get("value", "0")).isdigit()]
    for o in rows:
        if low(o["from"]) != addr or low(o["to"]) != target or int(o["value"]) <= 0:
            continue
        ob, ov = int(o["blockNumber"]), int(o["value"])
        for i in inc:
            ib, iv = int(i["blockNumber"]), int(i["value"])
            if asset(i) != asset(o) or not 0 <= ob - ib <= FWD_BLOCKS or iv < ov:
                continue
            if iv - ov <= (FWD_NATIVE if asset(o) == "native" else iv * FWD_TOKEN):
                return True
    return False


def classify(addr, txs, toks, tags, is_contract, busy, keep=lambda r: True):
    """deposit_addresses.py:104-168, returning diagnostics instead of None."""
    if is_contract(addr):
        return {"verdict": "not", "reason": "contract (has code)"}
    if txs is not None and len(txs) >= MAX_TXS:
        return {"verdict": "not", "reason": f"txlist >= {MAX_TXS}"}
    rows = [r for r in (txs or []) + toks if keep(r)]
    senders = {low(r["from"]) for r in rows if low(r["to"]) == addr and r.get("from")} - {addr}
    out = Counter(low(r["to"]) for r in rows if low(r["from"]) == addr and r.get("to"))
    res = {"rows": len(rows), "senders": len(senders), "out_rows": sum(out.values()),
           "top3": [(t[:10], n, exchange(tags, t) or "") for t, n in out.most_common(TOP)]}
    if not senders or len(senders) > MAX_SENDERS:
        return {**res, "verdict": "not", "reason": f"senders {len(senders)} not in 1..{MAX_SENDERS}"}
    if not out:
        return {**res, "verdict": "not", "reason": "no outgoing row"}
    total, hot = sum(out.values()), []
    for t, n in out.most_common(TOP):
        if exchange(tags, t):
            hot.append((t, n, True))
        elif not is_contract(t) and forwards(rows, addr, t) and busy(t):
            hot.append((t, n, False))
    share = sum(n for _t, n, _l in hot) / total
    lab = sum(n for _t, n, l in hot if l) / total
    res.update(share=round(share, 3), labelled_share=round(lab, 3),
               sweep_targets=[(t[:10], "label" if l else "activity") for t, _n, l in hot])
    if not hot or share < MIN_SHARE:
        return {**res, "verdict": "not", "reason": f"hot-wallet share {share:.2f} < {MIN_SHARE}"}
    ent = sorted({exchange(tags, t) for t, _n, l in hot if l})
    return {**res, "verdict": "scored" if lab >= MIN_SHARE else "context", "exchange": ", ".join(ent),
            "reason": "deposit address"}


def report_rule(addr, txs, toks, tags):
    """Behaviour rule of the report (verify.py checks 4-6) with the exchange names generalised."""
    outs = [r for r in toks if low(r["from"]) == addr and low(r["contractAddress"]) in (USDC, USDCE) and int(r["value"]) > 0]
    ins = [r for r in toks if low(r["to"]) == addr and low(r["contractAddress"]) in (USDC, USDCE) and int(r["value"]) > 0]
    gas = [r for r in (txs or []) if low(r["to"]) == addr and int(r["value"]) > 0]
    sinks = {low(r["to"]) for r in outs}
    sweep = bool(outs) and all(exchange(tags, s) for s in sinks)
    funder = bool(gas) and all(any("Deposit Funder" in n for n, _ in tags.get(low(g["from"]), [])) for g in gas)
    full = bool(outs) and abs(sum(int(r["value"]) for r in outs) - sum(int(r["value"]) for r in ins)) < 10**6
    if sweep and (funder or full):
        cls = "exchange deposit"
    elif len(sinks) == 1:
        cls = "single sink (customer-specific)"
    else:
        cls = "not classified"
    return {"class": cls, "sinks": len(sinks), "outflows": len(outs), "exchange_sweep": sweep,
            "gas_from_labelled_funder": funder if txs is not None else "no txlist", "full_forward": full,
            "exchange": ", ".join(sorted({exchange(tags, s) for s in sinks if exchange(tags, s)}))}


def selftest():
    a, h, s = "0x" + "c" * 40, "0x" + "d" * 40, "0x" + "a" * 40
    tags = {h: [("Binance 1", "name")]}
    nat = [{"from": s, "to": a, "value": str(10**18), "blockNumber": "1"},
           {"from": a, "to": h, "value": str(10**18 - 10**15), "blockNumber": "2"}]
    assert classify(a, nat, [], tags, lambda x: None, lambda x: False)["verdict"] == "scored"
    assert classify(a, nat, [], {}, lambda x: None, lambda x: True)["verdict"] == "context"
    assert classify(a, nat, [], {}, lambda x: None, lambda x: False)["verdict"] == "not"
    # a token sweep signed by the deposit address leaves a txlist row to the token contract too
    tok = [{"from": s, "to": a, "value": "100", "blockNumber": "1", "contractAddress": USDC},
           {"from": a, "to": h, "value": "100", "blockNumber": "2", "contractAddress": USDC}]
    call = [{"from": a, "to": USDC, "value": "0", "blockNumber": "2"}]
    assert classify(a, call, tok, tags, lambda x: x == USDC, lambda x: False)["share"] == 0.5


def main(this, prev):
    selftest()
    dirs, tags = [this, prev], load_tags([this, prev])
    cent = lambda r: (asset(r) == "native" and int(r["value"]) > 0) or (
        asset(r) in STABLE and int(r["value"]) >= 10 ** max(int(r.get("tokenDecimal") or 6) - 2, 0))

    def contract_check(signers, aware7702):
        def check(a):
            if a in CONTRACTS or (a in EIP7702 and not aware7702):
                return True
            return False if a in signers else None  # None = unknown, which the demixer does not reject
        return check

    out = {}
    for addr, (cls, desc, src) in CASES.items():
        txs, toks = load_pages(dirs, addr)
        signers = {addr} if txs and any(low(r["from"]) == addr for r in txs) else set()
        V = {
            "A_as_written": classify(addr, txs, toks, tags, contract_check(signers, False), lambda t: False),
            "B_as_written_busy_assumed": classify(addr, txs, toks, tags, contract_check(signers, False), lambda t: True),
            "C_polygon_adapted": classify(addr, txs, toks, tags, contract_check(signers, True), lambda t: True, cent),
            "D_adapted_contracts_unknown": classify(addr, txs, toks, tags, lambda a: None, lambda t: True, cent),
        }
        mine = [r for r in (txs or []) + toks if low(r["from"]) == addr]
        call = sum(1 for r in mine if "tokenDecimal" not in r and int(r["value"]) == 0)
        real = sum(1 for r in mine if cent(r))
        sweeps = [int(r["blockNumber"]) for r in toks if low(r["from"]) == addr and cent(r)]
        gas = [int(r["blockNumber"]) for r in (txs or []) if low(r["to"]) == addr and int(r["value"]) > 0]
        out[addr] = {"report_class": cls, "report": desc, "pages_from": src, "txlist": txs is not None,
                     "outgoing_rows": {"token_call_rows_in_txlist": call, "real_transfers": real,
                                       "zero_value_or_fake_token": len(mine) - call - real},
                     # descriptive: outflows with a native top-up in the 300 blocks before them
                     "outflows_after_gas_topup": f"{sum(any(0 < b - g <= 300 for g in gas) for b in sweeps)}/{len(sweeps)}"
                     if txs is not None else "no txlist",
                     "variants": V, "report_rule": report_rule(addr, txs, toks, tags)}
    # 0xef3aeff9 (BSC): only nonce reads are archived; the demixer's gates are applied to them.
    nonces = {int(p.name[:-5].split("_")[-1]): int(json.loads(p.read_text())["result"], 16)
              for p in (this / "evidence" / "bsc").glob("nonce_0xef3aeff9_*.json") if not p.name.endswith(".meta.json")}
    out["0xef3aeff9a5f61c6dda33069c58c1434006e13b20"] = {
        "report_class": "service", "report": "exchange hot wallet by nonce growth (BSC)", "nonces": nonces,
        "gate_txlist_ge_1000": min(nonces.values()) >= MAX_TXS, "busy_ge_10000": min(nonces.values()) >= HOT_TXS}
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
