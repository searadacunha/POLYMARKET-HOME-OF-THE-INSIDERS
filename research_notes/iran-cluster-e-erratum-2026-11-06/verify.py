"""Offline check of the erratum. Needs this folder and ../iran-cluster-e-network-2026-11-05/. python3 -I -B verify.py"""
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NET = HERE.parent / "iran-cluster-e-network-2026-11-05"
BYB = "0x93b7e169b93ece646d08cedbb8fa505796a5b96b"
REAL = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e",
        "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT0"}
checks = []


def check(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})


def tags():
    out = {}
    for f in sorted((NET / "evidence" / "http").glob("bs_meta_137_*.json")) + [HERE / "evidence" / "bs_meta_137.json"]:
        if f.name.endswith(".meta.json"):
            continue
        for a, v in (json.loads(f.read_text()).get("addresses") or {}).items():
            out.setdefault(a.lower(), set()).update(t["name"] for t in v.get("tags", []))
    return out


m = json.loads((HERE / "evidence" / "bs_meta_137.meta.json").read_text())
check("evidence_sha256", hashlib.sha256((HERE / "evidence" / "bs_meta_137.json").read_bytes()).hexdigest() == m["sha256"])
T = tags()
rows = [t for f in sorted((NET / "evidence" / "etherscan").glob(f"137_tokentx_{BYB}_p*.json")) if not f.name.endswith(".meta.json")
        for t in json.loads(f.read_text())["result"]]
outs = [t for t in rows if t["from"].lower() == BYB and t["contractAddress"].lower() in REAL and int(t["value"]) > 0]
by_token = {}
for t in outs:
    by_token.setdefault(REAL[t["contractAddress"].lower()], set()).add(t["to"].lower())
fake = [t for t in rows if t["from"].lower() == BYB and t["contractAddress"].lower() not in REAL]
usdt0 = sorted((t["to"].lower(), int(t["value"]) / 1e6) for t in outs if REAL[t["contractAddress"].lower()] == "USDT0")
check("usdt0_outflows", usdt0 == [("0x1347378b1d0eb69d3462e09b3dfa2fe28ebe74ec", 700.699999), ("0xa85c29b94f8a22a7268facee89ef4eca051be2ce", 3466.798977),
                                  ("0xf89d7b9c864f589bbf53a82105107622b35eaa40", 1000.999999)], usdt0)
check("usdt0_recipients_labelled_bybit", all(any("Bybit" in x for x in T.get(a, ())) for a, _ in usdt0),
      {a: sorted(T.get(a, ())) for a, _ in usdt0})
check("every_real_token_outflow_to_bybit", outs and all(any("Bybit" in x for x in T.get(t["to"].lower(), ())) for t in outs),
      {k: len(v) for k, v in by_token.items()})
check("other_rows_are_fake_tokens", all(t["contractAddress"].lower() not in REAL for t in fake), f"{len(fake)} rows of look-alike tokens")
src = (NET / "REPORT.md").read_text()
vsrc = (NET / "verify.py").read_text()
check("report_wording_found", "is checked by `verify.py` independently of the labels" in src)
check("verify_checks_use_tags", 'tagged(137, "0x9430801ebaf509ad49202aabc5f5bc6fd8a3daf8", "Binance: Deposit Funder")' in vsrc
      and 'tagged(137, g["from"], "Bybit: Deposit Funder")' in vsrc)
out = {"passed": sum(c["pass"] for c in checks), "total": len(checks), "checks": checks}
(HERE / "verification.json").write_text(json.dumps(out, indent=1, default=sorted))
print(f"{out['passed']}/{out['total']} checks passed")
for c in checks:
    if not c["pass"]:
        print("FAIL", c["check"], c["detail"])
sys.exit(0 if out["passed"] == out["total"] else 1)
