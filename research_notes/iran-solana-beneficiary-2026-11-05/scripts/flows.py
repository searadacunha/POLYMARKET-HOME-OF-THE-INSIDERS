"""Décode l'historique brut d'une adresse Solana (pages gTFA archivées) : une ligne par transaction.

python3 -I flows.py <raw_dir> <adresse> [--json out.json]
Hors ligne : ne lit que les fichiers archivés.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

SYSTEM = "11111111111111111111111111111111"
MEMO = {"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "Memo1UhkJRfHyvLMcVucJwxXeuD728EvVP4q1HGAqTB6"}


def keys_of(tx):
    ak = tx["transaction"]["message"]["accountKeys"]
    return [k["pubkey"] if isinstance(k, dict) else k for k in ak] + \
        [*tx["meta"].get("loadedAddresses", {}).get("writable", []), *tx["meta"].get("loadedAddresses", {}).get("readonly", [])]


def programs(tx):
    out = []
    ins = tx["transaction"]["message"]["instructions"]
    inner = [i for g in tx["meta"].get("innerInstructions") or [] for i in g["instructions"]]
    for i in ins + inner:
        p = i.get("programId")
        if p and p not in out:
            out.append(p)
    return out


def memos(tx):
    out = []
    for i in tx["transaction"]["message"]["instructions"]:
        if i.get("programId") in MEMO:
            out.append(i.get("parsed") if isinstance(i.get("parsed"), str) else i.get("data"))
    return out


def sol_transfers(tx):
    """Transferts SystemProgram (instructions et CPI), décodés par le nœud (jsonParsed)."""
    out = []
    ins = tx["transaction"]["message"]["instructions"]
    inner = [i for g in tx["meta"].get("innerInstructions") or [] for i in g["instructions"]]
    for i in ins + inner:
        p = i.get("parsed")
        if i.get("programId") == SYSTEM and isinstance(p, dict) and p.get("type") in ("transfer", "transferWithSeed", "createAccount"):
            inf = p["info"]
            out.append({"type": p["type"], "from": inf.get("source"), "to": inf.get("destination") or inf.get("newAccount"),
                        "lamports": int(inf["lamports"])})
    return out


def token_deltas(tx):
    pre = {b["accountIndex"]: b for b in tx["meta"].get("preTokenBalances") or []}
    post = {b["accountIndex"]: b for b in tx["meta"].get("postTokenBalances") or []}
    out = []
    for idx in sorted(set(pre) | set(post)):
        b = post.get(idx) or pre[idx]
        a0 = int(pre[idx]["uiTokenAmount"]["amount"]) if idx in pre else 0
        a1 = int(post[idx]["uiTokenAmount"]["amount"]) if idx in post else 0
        if a1 != a0:
            out.append({"mint": b["mint"], "owner": b.get("owner"), "account_index": idx,
                        "delta_raw": a1 - a0, "decimals": b["uiTokenAmount"]["decimals"]})
    return out


def rows(raw_dir: Path, addr: str):
    seen, out = set(), []
    for f in sorted(raw_dir.glob("gtfa_*_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for tx in json.loads(f.read_text())["result"]["data"]:
            sig = tx["transaction"]["signatures"][0]
            if sig in seen:
                continue
            seen.add(sig)
            k = keys_of(tx)
            m = tx["meta"]
            i = k.index(addr) if addr in k else None
            deltas = {k[j]: m["postBalances"][j] - m["preBalances"][j] for j in range(len(m["preBalances"]))}
            out.append({
                "signature": sig, "slot": tx["slot"], "tx_index": tx.get("transactionIndex"), "block_time": tx["blockTime"],
                "utc": datetime.fromtimestamp(tx["blockTime"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "err": m["err"], "fee": m["fee"], "fee_payer": k[0],
                "signers": [x["pubkey"] for x in tx["transaction"]["message"]["accountKeys"] if isinstance(x, dict) and x.get("signer")],
                "pre_lamports": m["preBalances"][i] if i is not None else None,
                "post_lamports": m["postBalances"][i] if i is not None else None,
                "delta_lamports": deltas.get(addr, 0),
                "sol_deltas": {a: d for a, d in deltas.items() if d},
                "sol_transfers": sol_transfers(tx), "token_deltas": token_deltas(tx),
                "programs": programs(tx), "memos": memos(tx), "source_file": f.name,
            })
    out.sort(key=lambda r: (r["slot"], r["tx_index"] or 0))
    return out


if __name__ == "__main__":
    raw_dir, addr = Path(sys.argv[1]), sys.argv[2]
    R = rows(raw_dir, addr)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(R, indent=1))
    for r in R:
        if r["err"] is None and r["delta_lamports"] == 0 and not any(t["owner"] == addr for t in r["token_deltas"]):
            continue
        cp = [(t["to"] if t["from"] == addr else t["from"], t["lamports"]) for t in r["sol_transfers"] if addr in (t["from"], t["to"])]
        print(r["utc"], r["slot"], r["signature"][:10], "err" if r["err"] else "ok",
              f'{(r["pre_lamports"] or 0)/1e9:.9f}->{(r["post_lamports"] or 0)/1e9:.9f}' + ('' if r["pre_lamports"] is not None else '(token-acct)'), f'{r["delta_lamports"]/1e9:+.9f}',
              "payer", r["fee_payer"][:6], "cp", [(c[:8], l / 1e9) for c, l in cp][:4],
              "tok", [(t["mint"][:6], t["owner"][:6] if t["owner"] else None, t["delta_raw"]) for t in r["token_deltas"]][:3],
              "prog", [p[:6] for p in r["programs"] if p not in (SYSTEM,)][:5], "memo", r["memos"][:1])
