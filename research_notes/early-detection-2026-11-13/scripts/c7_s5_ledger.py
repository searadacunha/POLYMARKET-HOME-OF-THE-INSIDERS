# Step 5: native-USDC ledger of the funder with running balance (integers in 1e-6 units), plus net result.
from lib import *
import json, datetime, csv
from decimal import Decimal
REPO = "/Volumes/PHI-Data/Projects/Polymarket-early-detection-20261113/investigations/followup-20261113/sources/data/"
s2 = json.load(open(P("s2_funder_transfers.json")))
proxies = {r["proxy"].lower(): r["handle"] for r in csv.DictReader(open(REPO + "nobel_accounts.csv"))}
rows = [r for r in s2["rows"] if r["amount_raw"] > 0]          # zero-value rows are poisoning events, not value
def kind(r):
    if r["dir"] == "out":
        if r["to"] in proxies: return "fund_proxy"
        if r["to"] == "0x9295ee1d8c5b022be115a2ad3c30c72e34e7f096": return "exit_across"
        return "exit_direct"
    if r["from"] == "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222": return "withdrawal_in"
    if r["tx_from"].lower() == FUNDER: return "other_in"
    if r["from"] == "0x07ae8551be970cb1cca11dd7a11f47ae82e70e67": return "capital_in"
    return "third_party_dust_in"
rows.sort(key=lambda r: (r["block"], r["logIndex"]))
bal = 0; cum_out_fund = 0; led = []
CAP = None
for r in rows:
    k = kind(r); sign = 1 if r["dir"] == "in" else -1
    bal += sign * r["amount_raw"]
    if k == "capital_in": CAP = r["amount_raw"]
    if k == "fund_proxy": cum_out_fund += r["amount_raw"]
    assert bal >= 0, ("negative balance", r["tx"])
    led.append({"utc": datetime.datetime.utcfromtimestamp(r["ts"]).strftime("%Y-%m-%dT%H:%M:%SZ"), "block": r["block"], "tx": r["tx"], "kind": k, "from": r["from"], "to": r["to"], "handle": proxies.get(r["to"]) or proxies.get(r["from"]), "signed_amount_usdc": sign * r["amount_raw"] / 1e6, "running_balance_usdc": bal / 1e6,
                "funded_from_recycled": (k == "fund_proxy" and cum_out_fund > CAP), "cum_sent_to_proxies_usdc": cum_out_fund / 1e6})
agg = {}
for l in led: agg[l["kind"]] = round(agg.get(l["kind"], 0) + abs(l["signed_amount_usdc"]), 6)
cap = sum(r["amount_raw"] for r in rows if kind(r) == "capital_in"); sent = sum(r["amount_raw"] for r in rows if kind(r) == "fund_proxy")
back = sum(r["amount_raw"] for r in rows if kind(r) == "withdrawal_in"); ex = sum(r["amount_raw"] for r in rows if kind(r).startswith("exit"))
dust = sum(r["amount_raw"] for r in rows if kind(r) == "third_party_dust_in")
resid_chain = int(call_bal := hexint(r1("eth_call", [{"to": USDC, "data": "0x70a08231" + pad(FUNDER)[2:]}, "latest"])))
summary = {"external_capital": cap/1e6, "gross_sent_to_proxies": sent/1e6, "gross_received_from_withdrawals": back/1e6, "exits_total": ex/1e6, "third_party_dust_in": dust/1e6,
           "residual_balance_ledger": bal/1e6, "residual_balance_balanceOf_latest": resid_chain/1e6,
           "net_funder_level_excl_dust": (ex - cap)/1e6, "net_funder_level_residual_incl": (ex + bal - cap)/1e6,
           "net_funder_level_residual_excl_dust": (ex + (bal - dust) - cap)/1e6,
           "check_returned_minus_sent": (back - sent)/1e6,
           "first_funding_exceeding_capital": next((l["tx"] for l in led if l["funded_from_recycled"]), None),
           "n_fundings_paid_with_recycled": sum(l["funded_from_recycled"] for l in led)}
assert cap + back + dust - sent - ex == bal
print(json.dumps(summary, indent=1)); 
json.dump({"summary": summary, "ledger": led}, open(P("s5_ledger.json"), "w"), indent=1)
with open(P("s5_ledger.csv"), "w") as f:
    w = csv.DictWriter(f, fieldnames=list(led[0])); w.writeheader(); w.writerows(led)
for l in led: print(l["utc"], l["kind"].ljust(20), str(l["handle"]).ljust(16), f'{l["signed_amount_usdc"]:>16,.6f} {l["running_balance_usdc"]:>16,.6f}', "RECYCLED" if l["funded_from_recycled"] else "")
