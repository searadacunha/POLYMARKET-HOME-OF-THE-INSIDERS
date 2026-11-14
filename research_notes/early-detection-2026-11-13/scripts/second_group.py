"""Second linked group of the Machado market (Nobel Peace Prize 2025): how each file of data/ was produced.

Network needed (public, keyless): data-api.polymarket.com, gamma-api.polymarket.com, Polygon JSON-RPC.
Run from the repository root:

    python3 research_notes/early-detection-2026-11-13/scripts/second_group.py OUT_DIR

Steps, each writing one file in OUT_DIR:
  funding      direct collateral payers of six accounts outside the documented group   nobel_new_accounts_funding.json
  upstream     who paid the two owner keys (the documented funder is the control)        nobel_owner_keys_upstream.json
  hub          every collateral transfer in and out of the common payer, 7-16 Oct 2025   payer_36626_flows.json
  accounts     owners, Machado position, deposits and withdrawals of the three accounts  second_cluster_accounts.json
  circuit      receipts of every transaction of the circuit, transfer by transfer        second_cluster_edges.csv
  graph        direct account-to-account transfers among the 45 largest buyers           nobel_top_buyers_direct_graph.json

Addresses are never typed: prefixes are resolved from data/machado_top45_accumulators.csv with a uniqueness check, and
every other address comes out of a previous step. An address is not a person; a transfer says who paid, not who decided.
"""
import calendar, collections, csv, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "monitoring"))
from phi_monitor import chain, collect, net, store   # noqa: E402

DATA = os.path.join(HERE, "..", "data")
CONDITION = "0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d"
C7_FUNDER = "0xe206961002feebd9edb152eed9b630a351874043"       # investigations/followup-20261113, F-001
API = "https://data-api.polymarket.com/v2/activity"
utc = lambda t: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(int(t)))


def top45():
    with open(os.path.join(DATA, "machado_top45_accumulators.csv")) as f:
        return list(csv.DictReader(f))


def resolve(prefix, rows):
    hit = [r["wallet"] for r in rows if r["wallet"].startswith(prefix)]
    if len(hit) != 1:
        raise SystemExit(f"prefix {prefix} resolves to {len(hit)} wallets")
    return hit[0]


def ts(iso):
    return calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))


def activity(wallet, **params):
    """Every row of one activity query (cursor followed to the end; an unfinished pagination raises)."""
    q = "&".join(f"{k}={v}" for k, v in params.items()); rows, cursor = [], None
    for _ in range(60):
        j = net.get_json(f"{API}?user={wallet}&limit=500&sort_by=TIMESTAMP&exclude_deposits_withdrawals=false&{q}" + (f"&cursor={cursor}" if cursor else ""))
        rows += j.get("data") or []; cursor = (j.get("pagination") or {}).get("next_cursor")
        if not (j.get("pagination") or {}).get("has_more") or not cursor:
            return rows
    raise RuntimeError(f"pagination not finished for {wallet} {q}")


def step_funding(out):
    rows = top45(); con = store.connect(":memory:"); res = []
    for prefix in ("0x5a8e6f7f", "0x870f371b", "0x2ed75fea", "0xa0f16053", "0x551e72ed", "0x9db778f4"):
        w = resolve(prefix, rows); r = next(x for x in rows if x["wallet"] == w); t_first = ts(r["first_yes_buy_utc"])
        base = collect.baseline(con, w, t_first)
        fund = collect.funding(con, w, max(t_first - 72 * 3600, (base["first_activity"] or t_first) - 2 * 3600), t_first)
        res.append({"wallet": w, "first_yes_buy_utc": r["first_yes_buy_utc"], "buy_cash": float(r["yes_buy_cash_usd"]), "prior_markets": base["prior_markets"],
                    "safe_owners": chain.safe_owners(w),
                    "funding": [{"utc": utc(x["ts"]), "payer": x["payer"], "kind": x["payer_kind"], "nonce_then": x["payer_nonce"], "token": x["token"],
                                 "amount": x["amount"], "tx": x["tx"]} for x in fund]})
    json.dump(res, open(os.path.join(out, "nobel_new_accounts_funding.json"), "w"), indent=1)
    return res


def step_upstream(out, funding):
    """Collateral received by each owner key in the 48 h before it paid its account. The documented funder is the control."""
    keys = {C7_FUNDER: 1760049619}
    for r in funding[:2]:                                        # the two accounts paid by their own owner key
        own = [x for x in r["funding"] if x["payer"] in (r["safe_owners"] or [])]
        keys[own[0]["payer"]] = ts(own[0]["utc"])
    res = {}
    for key, t_pay in keys.items():
        b1 = chain.block_at(t_pay); ins = chain.transfers_to(key, chain.block_at(t_pay - 48 * 3600), b1 + 5)
        res[key] = {"t_pay_utc": utc(t_pay), "inflows": [dict(x, utc=utc(x["ts"] or chain.block_ts(x["block"])), payer_kind=chain.account_kind(x["payer"], x["block"])) for x in ins]}
    json.dump(res, open(os.path.join(out, "nobel_owner_keys_upstream.json"), "w"), indent=1)
    return res


def step_hub(out, hub, t0=1759795200, t1=1760572800):
    b0, b1 = chain.block_at(t0), chain.block_at(t1); topic = "0x" + "0" * 24 + hub[2:]

    def logs(topics):
        res = []
        for a in range(b0, b1 + 1, 40000):
            res += net.rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(b1, a + 39999)), "address": chain.STABLES, "topics": topics}], urls=chain.WIDE_RPC)
        return [{"block": int(l["blockNumber"], 16), "ts": chain.block_ts(int(l["blockNumber"], 16)), "tx": l["transactionHash"], "from": "0x" + l["topics"][1][-40:],
                 "to": "0x" + l["topics"][2][-40:], "token": l["address"].lower(), "amount": int(l["data"], 16) / 1e6} for l in res if int(l["data"], 16) > 0]
    res = {"address": hub, "window_utc": [utc(t0), utc(t1)], "out": logs([chain.TRANSFER, topic]), "in": logs([chain.TRANSFER, None, topic])}
    json.dump(res, open(os.path.join(out, "payer_36626_flows.json"), "w"), indent=1)
    return res


def step_accounts(out, wallets):
    res = {}
    for w, label in wallets.items():
        acts = activity(w, sort_direction="ASC", start=1759881600, end=1761004800)
        mach = [a for a in acts if a.get("type") == "TRADE" and a.get("condition_id") == CONDITION and a.get("outcome") == "Yes"]
        res[w] = {"label": label, "owners": chain.safe_owners(w),
                  "machado_buy": sum(float(a["usdc_size"]) for a in mach if a["side"] == "BUY"), "machado_sell": sum(float(a["usdc_size"]) for a in mach if a["side"] == "SELL"),
                  "net_yes": sum(float(a["size"]) * (1 if a["side"] == "BUY" else -1) for a in mach),
                  "redeem": sum(float(a["usdc_size"]) for a in acts if a.get("type") == "REDEEM" and a.get("condition_id") == CONDITION),
                  "deposits": [{"ts": a["timestamp"], "usdc": a["usdc_size"], "tx": a["transaction_hash"]} for a in acts if a.get("type") == "DEPOSIT"],
                  "withdrawals": [{"ts": a["timestamp"], "usdc": a["usdc_size"], "tx": a["transaction_hash"]} for a in acts if a.get("type") == "WITHDRAWAL"]}
    json.dump(res, open(os.path.join(out, "second_cluster_accounts.json"), "w"), indent=1)
    return res


def step_circuit(out, acc, hub, t0=1760077800, t1=1760148000):
    a, b, c = list(acc); ka, kb = acc[a]["owners"][0], acc[b]["owners"][0]
    lab = {a: "account A (fresh)", b: "account B (fresh)", c: "account C (established)", ka: "owner key of A", kb: "owner key of B", hub["address"]: "hub key"}
    txs = {d["tx"] for p in acc for k in ("deposits", "withdrawals") for d in acc[p][k] if t0 <= int(d["ts"]) <= t1}
    txs |= {x["tx"] for x in hub["out"] + hub["in"] if t0 <= x["ts"] <= t1}
    b0, b1 = chain.block_at(t0), chain.block_at(t1)
    for addr in (a, b, ka, kb):
        txs |= {x["tx"] for x in chain.transfers_to(addr, b0, b1)}
    rows = []
    for tx in txs:
        rc = net.rpc("eth_getTransactionReceipt", [tx], urls=chain.WIDE_RPC); when = chain.block_ts(int(rc["blockNumber"], 16))
        for l in rc["logs"]:
            if l["topics"][0] == chain.TRANSFER and len(l["topics"]) == 3 and l["address"].lower() in chain.STABLES and int(l["data"], 16) > 0:
                s, d = "0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:]
                rows.append({"utc": utc(when), "block": int(rc["blockNumber"], 16), "tx": tx, "log_index": int(l["logIndex"], 16), "from": s, "to": d,
                             "from_label": lab.get(s, ""), "to_label": lab.get(d, ""), "token": l["address"].lower(), "amount": int(l["data"], 16) / 1e6})
    rows.sort(key=lambda r: (r["block"], r["log_index"]))
    with open(os.path.join(out, "second_cluster_edges.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows


def step_graph(out):
    """A transaction hash seen as WITHDRAWAL of one account and DEPOSIT of another is a direct transfer between them."""
    acc = {r["wallet"]: {"buy_cash": float(r["yes_buy_cash_usd"]), "first": r["first_yes_buy_utc"], "tag": r["documented_handle"]} for r in top45()}
    feeds = {p: [(t, a["transaction_hash"], int(a["timestamp"]), float(a["usdc_size"])) for t in ("DEPOSIT", "WITHDRAWAL")
                 for a in activity(p, sort_direction="DESC", type=t)] for p in acc}
    wd = {p: {r[1] for r in rows if r[0] == "WITHDRAWAL"} for p, rows in feeds.items()}
    edges = collections.defaultdict(list)
    for b, rows in feeds.items():
        for typ, tx, when, usdc in rows:
            if typ == "DEPOSIT":
                for a in acc:
                    if a != b and tx in wd[a]:
                        edges[f"{a}>{b}"].append({"utc": utc(when), "usdc": usdc, "tx": tx})
    adj = collections.defaultdict(set)
    for k in edges:
        a, b = k.split(">"); adj[a].add(b); adj[b].add(a)
    seen, comps = set(), []
    for n in adj:
        if n not in seen:
            comp, stack = set(), [n]
            while stack:
                x = stack.pop()
                if x not in comp:
                    comp.add(x); stack += list(adj[x] - comp)
            seen |= comp; comps.append(sorted(comp))
    json.dump({"accounts": acc, "edges": edges, "components": comps}, open(os.path.join(out, "nobel_top_buyers_direct_graph.json"), "w"), indent=1)


def main(out):
    os.makedirs(out, exist_ok=True)
    funding = step_funding(out)
    up = step_upstream(out, funding)
    payers = {x["payer"] for k, v in up.items() if k != C7_FUNDER for x in v["inflows"]}
    if len(payers) != 1:
        raise SystemExit(f"expected one common payer of the two owner keys, found {sorted(payers)}")
    hub = step_hub(out, payers.pop())
    third = [x["to"] for x in hub["out"] if chain.account_kind(x["to"])["kind"] == "contract" and x["amount"] > 20000]
    acc = step_accounts(out, {funding[0]["wallet"]: "fresh A", funding[1]["wallet"]: "fresh B", third[0]: "established C"})
    step_circuit(out, acc, hub)
    step_graph(out)
    print("done; requests:", dict(net.COUNTS))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "second_group_out")
