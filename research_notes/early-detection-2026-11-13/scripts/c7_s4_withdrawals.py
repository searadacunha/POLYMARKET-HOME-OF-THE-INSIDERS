# Step 4: the 16 Relay withdrawals: receipt decode, delivery matching on chain.
from lib import *
import json, csv
REPO = "/Volumes/PHI-Data/Projects/Polymarket-early-detection-20261113/investigations/followup-20261113/sources/data/"
W = list(csv.DictReader(open(REPO + "nobel_relay_withdrawals.csv")))
acc = {r["proxy"].lower(): r["handle"] for r in csv.DictReader(open(REPO + "nobel_accounts.csv"))}
s2 = json.load(open(P("s2_funder_transfers.json")))
inn = {r["tx"]: r for r in s2["rows"] if r["dir"] == "in"}
tokinfo = {}
def tok(a):
    if a in tokinfo: return tokinfo[a]
    def c(d):
        try: return r1("eth_call", [{"to": a, "data": d}, "latest"])
        except Exception: return None
    s = c("0x95d89b41"); dc = c("0x313ce567")
    sym = None
    if s and len(s) > 130:
        b = bytes.fromhex(s[2:]); n = int.from_bytes(b[32:64], "big"); sym = b[64:64+n].decode(errors="replace")
    tokinfo[a] = {"symbol": sym, "decimals": hexint(dc) if dc and dc != "0x" else None}
    return tokinfo[a]
res = []
assert len(W) == 16 and len({w["in_tx"] for w in W}) == 16
for w in W:
    h = w["in_tx"]; proxy = w["proxy"].lower(); rec = w["recipient"].lower()
    rc = r1("eth_getTransactionReceipt", [h]); t = r1("eth_getTransactionByHash", [h])
    blk = hexint(rc["blockNumber"]); bts = hexint(r1("eth_getBlockByNumber", [hex(blk), False])["timestamp"])
    tl = []
    for l in rc["logs"]:
        if len(l["topics"]) == 3 and l["topics"][0] == TRANSFER:
            ti = tok(l["address"])
            dc = ti["decimals"] if ti["decimals"] is not None else 6
            tl.append({"token": l["address"], "symbol": ti["symbol"], "from": "0x"+l["topics"][1][-40:], "to": "0x"+l["topics"][2][-40:], "amount": int(l["data"], 16)/10**dc, "logIndex": hexint(l["logIndex"])})
    left = [x for x in tl if x["from"] == proxy]
    deliv = [x for x in tl if x["token"].lower() == USDC and x["to"] == rec]
    d = {"handle": w["handle"], "proxy": proxy, "relay_created_utc": w["created_utc"], "recipient": rec, "csv_usdc": float(w["usdc"]), "tx": h, "status": rc["status"], "block": blk, "ts": bts,
         "tx_from": t["from"], "tx_to": t["to"], "selector": t["input"][:10], "leaving_proxy": left, "native_usdc_to_recipient": deliv, "n_transfer_logs": len(tl),
         "all_transfers": tl,
         "funder_incoming_list_match": (h in inn and inn[h]["to"] == FUNDER and abs(inn[h]["amount"] - float(w["usdc"])) < 5e-7) if rec == FUNDER else None}
    res.append(d)
    print(w["handle"], h[:12], d["status"], blk, [(x["symbol"], x["amount"], x["to"][:10]) for x in left], "deliv", [(x["amount"], x["from"][:10]) for x in deliv], d["funder_incoming_list_match"], flush=True)
json.dump({"tokens": tokinfo, "withdrawals": res}, open(P("s4_withdrawals.json"), "w"), indent=1)
