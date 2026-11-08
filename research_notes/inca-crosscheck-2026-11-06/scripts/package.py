"""Builds evidence/ (tracked) from the raw archive (outside git). Every evidence file keeps the URL and SHA-256 of
the raw responses it was made from. Polymarket rows are reduced: profile fields are dropped, and controls keep no
username. Run after build.py: python3 -I scripts/package.py"""
import gzip, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
sys.path.insert(0, str(HERE))
from collect import RAW  # noqa: E402
from build import S, INCA  # noqa: E402

E = NOTE / "evidence"
KEEP = ["proxy_wallet", "timestamp", "condition_id", "type", "size", "usdc_size", "transaction_hash", "price", "token_id",
        "side", "outcome_index", "title", "slug", "event_slug", "outcome"]
TAPE = ["proxy_wallet", "side", "token_id", "condition_id", "size", "price", "timestamp", "transaction_hash", "outcome"]
EXTRA_PM = ["0x283ad35049970a1d0ca4c766acfefa4f44f91298", "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3"]  # found on the way; reduced like a control


def meta(p):
    m = json.loads(p.with_name(p.name[:-5] + ".meta.json").read_text())
    body = p.read_bytes()
    assert hashlib.sha256(body).hexdigest() == m["sha256"], p
    return {"file": str(p.relative_to(RAW)), "sha256": m["sha256"], "url": m.get("url") or m.get("endpoint"),
            "fetched_utc": m["fetched_utc"]}


def pages(d, pat):
    return [p for p in sorted(d.glob(pat)) if not p.name.endswith(".meta.json")]


def write(path, obj, gz=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=None if gz else 1, sort_keys=True).encode()
    if gz:
        path.write_bytes(gzip.compress(data, mtime=0))
    else:
        path.write_bytes(data + b"\n")


def reduce_rows(rows, keep_name):
    return [{**{k: r.get(k) for k in KEEP}, **({"name": r.get("name")} if keep_name else {})} for r in rows]


def main():
    if E.exists():  # rebuilt from the raw archive each time
        import shutil; shutil.rmtree(E)
    hashes = set()
    for w in S + EXTRA_PM:
        keep = w in INCA
        for sub, pat, out in (("polymarket_dw", "p*.json", "polymarket_dw"), ("polymarket", "v2activity_p*.json", "polymarket_full")):
            d = RAW / sub / w
            if not (d / "DONE.json").exists():
                continue
            ps = pages(d, pat)
            rows = [r for p in ps for r in json.loads(p.read_text())["data"]]
            if sub == "polymarket" and not keep and w not in EXTRA_PM:
                # control read in full before amendment A1: keep only its deposit and withdrawal rows, for the A1 check
                rows, out = [r for r in rows if r["type"] in ("DEPOSIT", "WITHDRAWAL")], "polymarket_full_dw"
            write(E / out / f"{w}.json", {"wallet": w, "rows": reduce_rows(rows, keep), "raw": [meta(p) for p in ps],
                                          "done": json.loads((d / "DONE.json").read_text())})
            if w in S:  # every receipt of the analysed set is required; third parties keep only the receipts read
                hashes |= {r["transaction_hash"].lower() for r in rows if r["type"] in ("DEPOSIT", "WITHDRAWAL")}
    cond = json.loads((NOTE / "data" / "population.json").read_text())["condition"]
    ps = pages(RAW / "trades" / cond, "p*.json")
    write(E / f"trades_{cond[:10]}.json.gz", {"condition": cond, "rows": [{k: r.get(k) for k in TAPE} for p in ps
                                                                          for r in json.loads(p.read_text())["data"]],
                                             "raw": [meta(p) for p in ps]}, gz=True)
    rec = []
    for p in sorted((RAW / "polygon").glob("*.eth_getTransactionReceipt.json")):
        h = p.name.split(".")[0]
        tx = RAW / "polygon" / f"{h}.eth_getTransactionByHash.json"
        rec.append({"hash": h, "receipt": json.loads(p.read_text())["result"], "receipt_raw": meta(p),
                    "tx": json.loads(tx.read_text())["result"] if tx.exists() else None, "tx_raw": meta(tx) if tx.exists() else None})
    missing = hashes - {r["hash"] for r in rec}
    if missing:
        raise SystemExit(f"{len(missing)} deposit or withdrawal receipts missing")
    write(E / "polygon_receipts.json.gz", rec, gz=True)
    for d in sorted((RAW / "relay").iterdir()):
        ps = pages(d, "p*.json")
        write(E / "relay" / f"{d.name}.json.gz", {"address": d.name, "requests": [q for p in ps for q in json.loads(p.read_text())["requests"]],
                                                "raw": [meta(p) for p in ps], "done": json.loads((d / "DONE.json").read_text())}, gz=True)
    for d in sorted((RAW / "etherscan").iterdir()):
        for action in ("tokentx", "txlist"):
            ps = pages(d, f"137_{action}_p*.json")
            if ps:
                cap = (d / f"137_{action}_CAPPED.json")
                write(E / "etherscan" / f"{d.name}_{action}.json.gz", {"address": d.name, "action": action, "capped": cap.exists(),
                      "rows": [r for p in ps for r in json.loads(p.read_text())["result"]], "raw": [meta(p) for p in ps]}, gz=True)
    for sub in ("blockscout", "polygon_code", "http"):
        for p in pages(RAW / sub, "*.json"):
            write(E / sub / p.name, {"body": json.loads(p.read_text()), "raw": meta(p)})
    sums = sorted((hashlib.sha256(p.read_bytes()).hexdigest(), str(p.relative_to(NOTE)))
                  for p in E.rglob("*") if p.is_file())
    (NOTE / "SHA256SUMS.txt").write_text("".join(f"{h}  {n}\n" for h, n in sums))
    print("evidence files", len(sums), "receipts", len(rec))


if __name__ == "__main__":
    main()
