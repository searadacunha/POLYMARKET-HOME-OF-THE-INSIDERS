"""Sequential collector (1 network worker), adapted from PR 27's iran-solana-beneficiary collector.
Archives every raw response with a meta file (no key) and its SHA-256. Raw data outside git.

Added: `sigs <address>` (public Solana RPC getSignaturesForAddress, all pages) and `evm <chain> <hash>` (receipt and tx).

Usage :
  python3 -I collect.py sol-history <adresse> [--gte UNIX] [--lte UNIX] [--max-pages N]
  python3 -I collect.py sol-tx <signature>
  python3 -I collect.py relay <hash_ou_sig>
  python3 -I collect.py http <nom> <url>        # GET public (Blockscout, Polymarket data-api)
"""
import hashlib, json, os, re, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(os.environ.get("BRIDGES_RAW", Path.home() / "Projects/Polymarket-inca-bridges-raw-20261106/raw"))
_KEY = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
UA = {"content-type": "application/json", "user-agent": "inca-bridges-research/1.0"}


def keys():
    cfg = json.loads((Path.home() / ".config/forensics_v2/helius_sources.json").read_text())
    ok, out = set(cfg["pool_fingerprints"]), []
    for s in cfg["sources"]:
        p = Path(s["path"]).expanduser()
        if p.exists():
            for k in _KEY.findall(p.read_text(errors="replace")):
                if hashlib.sha256(k.encode()).hexdigest()[:8] in ok and k not in out:
                    out.append(k)
    if not out:
        raise SystemExit("aucune clé du pool")
    return out


def scrub(t):
    return _KEY.sub("<KEY>", t)


def archive(path: Path, body: bytes, meta: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    meta = {**meta, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
            "fetched_utc": datetime.now(timezone.utc).isoformat()}
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=1))
    return meta


_K, _I, _DEAD = None, 0, set()


def rpc(method, params, out: Path, tries=8):
    global _K, _I
    _K = _K or keys()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    delay, last = 1.0, ""
    for _ in range(tries):
        live = [x for x in _K if x not in _DEAD] or _K
        k = live[_I % len(live)]; _I += 1
        req = urllib.request.Request(f"https://mainnet.helius-rpc.com/?api-key={k}", data=body, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw, status = r.read(), r.status
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {scrub(e.read()[:200].decode(errors='replace'))}"
            if "max usage" in last.lower():
                _DEAD.add(k); continue  # quota épuisé : clé suivante sans attendre
            if e.code == 400:
                raise SystemExit(f"{method}: {last}")
            time.sleep(delay); delay = min(delay * 2, 60); continue
        except Exception as e:  # réseau / timeout : on retente, jamais de None silencieux
            last = scrub(repr(e)); time.sleep(delay); delay = min(delay * 2, 60); continue
        payload = json.loads(raw)
        if "error" in payload:
            last = scrub(json.dumps(payload["error"])[:200])
            if payload["error"].get("code") == -32429 or "rate" in last.lower():
                time.sleep(delay); delay = min(delay * 2, 60); continue
            raise SystemExit(f"{method}: {last}")
        archive(out, raw, {"endpoint": "https://mainnet.helius-rpc.com/ (key redacted)", "method": method,
                           "params": params, "http_status": status})
        time.sleep(0.25)
        return payload["result"]
    raise SystemExit(f"{method}: échec après {tries} essais: {last}")


def sol_history(addr, gte=None, lte=None, max_pages=200):
    d = RAW / "sol" / addr
    opts = {"transactionDetails": "full", "sortOrder": "asc", "limit": 100, "encoding": "jsonParsed",
            "maxSupportedTransactionVersion": 0, "filters": {"tokenAccounts": "balanceChanged"}}
    if gte or lte:
        opts["filters"]["blockTime"] = {k: v for k, v in (("gte", gte), ("lte", lte)) if v}
    tag = f"{gte or 0}_{lte or 0}"
    n, tok, total = 0, None, 0
    while n < max_pages:
        o = dict(opts, **({"paginationToken": tok} if tok else {}))
        res = rpc("getTransactionsForAddress", [addr, o], d / f"gtfa_{tag}_p{n:03d}.json")
        total += len(res.get("data", []))
        tok = res.get("paginationToken"); n += 1
        if not tok or not res.get("data"):
            break
    term = "END" if not tok else "MAX_PAGES"
    (d / f"gtfa_{tag}_DONE.json").write_text(json.dumps({"pages": n, "txs": total, "termination": term}))
    print(addr, "pages", n, "txs", total, term)


def get(name, url, delay=0.5):
    out = RAW / "http" / f"{name}.json"
    req = urllib.request.Request(url, headers={"user-agent": UA["user-agent"], "accept": "application/json"})
    for i in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw, st = r.read(), r.status
            archive(out, raw, {"url": url, "http_status": st}); time.sleep(delay); return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(15 * (i + 1)); continue
            archive(out.with_name(out.stem + f".HTTP{e.code}.json"), e.read(), {"url": url, "http_status": e.code})
            raise SystemExit(f"{url}: HTTP {e.code}")
    raise SystemExit(f"{url}: échec")


def etherscan(chain, action, address):
    """Etherscan v2, clé lue sans être écrite (même source que l'enquête flow-trace). Pagination 1 000/page."""
    key = next(l.split("=", 1)[1].strip().strip("\"'") for l in (Path.home() / "Downloads/.env").read_text().splitlines()
               if l.startswith("ETHERSCAN_API_KEY="))
    rows, page = [], 1
    while True:
        q = f"chainid={chain}&module=account&action={action}&address={address}&page={page}&offset=1000&sort=asc"
        for i in range(6):
            with urllib.request.urlopen(urllib.request.Request(f"https://api.etherscan.io/v2/api?{q}&apikey={key}",
                                                               headers={"user-agent": UA["user-agent"]}), timeout=60) as r:
                raw = r.read()
            d = json.loads(raw)
            if d.get("status") == "1" or "No transactions found" in str(d.get("message")):
                break
            time.sleep(3 * (i + 1))  # « too busy » ou limite : jamais pris pour une liste vide
        else:
            raise SystemExit(f"etherscan {chain} {action} {address}: {str(d)[:200]}")
        archive(RAW / "etherscan" / f"{chain}_{action}_{address}_p{page}.json", raw,
                {"url": f"https://api.etherscan.io/v2/api?{q}&apikey=<KEY>", "status": d.get("status")})
        res = d.get("result") or []
        rows += res
        if len(res) < 1000:
            break
        page += 1; time.sleep(0.4)
    print(chain, action, address, len(rows))


PUBLIC_SOL = "https://api.mainnet-beta.solana.com"


def public_rpc(method, params, out: Path, tries=8):
    """Public Solana RPC (no key). An error or a missing result stops the run; it is never read as empty."""
    if out.exists():
        return json.loads(out.read_bytes())["result"]
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    delay = 2.0
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(PUBLIC_SOL, data=body, headers=UA), timeout=90) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(delay); delay = min(delay * 2, 60); continue
            raise SystemExit(f"{method}: HTTP {e.code}")
        except Exception:
            time.sleep(delay); delay = min(delay * 2, 60); continue
        payload = json.loads(raw)
        if "error" in payload or "result" not in payload:
            if "429" in json.dumps(payload.get("error", "")):
                time.sleep(delay); delay = min(delay * 2, 60); continue
            raise SystemExit(f"{method}: {json.dumps(payload.get('error'))[:200]}")
        archive(out, raw, {"endpoint": PUBLIC_SOL, "method": method, "params": params, "http_status": 200})
        time.sleep(1.2)
        return payload["result"]
    raise SystemExit(f"{method}: failed after {tries} tries")


def sigs(addr, max_pages=50):
    """Every signature of `addr` (newest first, 1,000 per page). Stops on a short page; MAX_PAGES is reported."""
    d, before, n, total = RAW / "sol" / addr, None, 0, 0
    while n < max_pages:
        o = {"limit": 1000, **({"before": before} if before else {})}
        res = public_rpc("getSignaturesForAddress", [addr, o], d / f"sigs_p{n:03d}.json")
        total += len(res); n += 1
        if len(res) < 1000:
            break
        before = res[-1]["signature"]
    term = "END" if n < max_pages else "MAX_PAGES"
    (d / "sigs_DONE.json").write_text(json.dumps({"pages": n, "sigs": total, "termination": term}))
    print(addr, "sigs", total, term)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "sigs":
        for x in a[1:]:
            sigs(x)
        sys.exit()
    if a[0] == "evm-tx":  # evm-tx <dir> <rpc url> <hash>...: receipt and transaction from the given node
        d, ep = RAW / a[1], a[2]
        for h in a[3:]:
            for m in ("eth_getTransactionReceipt", "eth_getTransactionByHash"):
                out = d / f"{h}.{m}.json"
                if out.exists():
                    continue
                body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": [h]}).encode()
                for i in range(6):
                    try:
                        if ep.startswith("etherscan:"):  # Etherscan v2 proxy module; the key is read, never archived
                            key = next(l.split("=", 1)[1].strip().strip("\"'") for l in
                                       (Path.home() / "Downloads/.env").read_text().splitlines()
                                       if l.startswith("ETHERSCAN_API_KEY="))
                            q = f"chainid={ep.split(':')[1]}&module=proxy&action={m}&txhash={h}"
                            req = urllib.request.Request(f"https://api.etherscan.io/v2/api?{q}&apikey={key}",
                                                         headers={"user-agent": UA["user-agent"]})
                        else:
                            req = urllib.request.Request(ep, data=body, headers=UA)
                        with urllib.request.urlopen(req, timeout=60) as r:
                            raw = r.read()
                        if json.loads(raw).get("result") is not None:
                            break
                    except Exception:
                        pass
                    time.sleep(2 * (i + 1))
                else:
                    raise SystemExit(f"{h} {m}: no result from {ep}")
                archive(out, raw, {"endpoint": ep, "method": m, "params": [h]})
                time.sleep(0.3)
        print("evm-tx", len(a) - 3, "done")
        sys.exit()
    if a[0] == "sol-txs":  # getTransaction (public RPC) for every signature listed in a file, one per line
        todo = [l.split()[0] for l in Path(a[1]).read_text().splitlines() if l.strip()]
        for i, sg in enumerate(todo):
            public_rpc("getTransaction", [sg, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
                       RAW / "sol" / "tx" / f"{sg}.json")
        print("sol-txs", len(todo), "done")
        sys.exit()
    if a[0] == "etherscan":
        etherscan(int(a[1]), a[2], a[3]); sys.exit()
    opt = lambda f: int(a[a.index(f) + 1]) if f in a else None
    if a[0] == "sol-history":
        sol_history(a[1], opt("--gte"), opt("--lte"), opt("--max-pages") or 200)
    elif a[0] == "sol-tx":
        rpc("getTransaction", [a[1], {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
            RAW / "sol" / "tx" / f"{a[1]}.json")
    elif a[0] == "relay":
        get(f"relay_{a[1]}", f"https://api.relay.link/requests/v2?hash={a[1]}", delay=13)
    elif a[0] == "http":
        get(a[1], a[2])
    elif a[0] == "poly-tx":  # reçu + transaction Polygon, nœud public
        for h in a[1:]:
            for m in ("eth_getTransactionReceipt", "eth_getTransactionByHash"):
                out = RAW / "polygon" / f"{h}.{m}.json"
                if out.exists():
                    continue
                body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": [h]}).encode()
                req = urllib.request.Request("https://polygon.drpc.org", data=body, headers=UA)
                with urllib.request.urlopen(req, timeout=60) as r:
                    raw = r.read()
                if json.loads(raw).get("result") is None:
                    raise SystemExit(f"{h} {m}: résultat vide (nœud à recouper)")
                archive(out, raw, {"endpoint": "https://polygon.drpc.org", "method": m, "params": [h]})
                time.sleep(0.3)
    elif a[0] == "pm-activity":  # toutes les lignes /v2/activity d'un compte, pagination par curseur
        cur, n, rows = None, 0, 0
        while True:
            u = (f"https://data-api.polymarket.com/v2/activity?user={a[1]}&limit=500&sort_by=TIMESTAMP"
                 f"&sort_direction=ASC&exclude_deposits_withdrawals=false" + (f"&cursor={cur}" if cur else ""))
            b = get(f"pm_v2activity_{a[1]}_p{n:03d}", u, delay=0.4)
            rows += len(b.get("data", [])); n += 1
            cur = (b.get("pagination") or {}).get("next_cursor")
            if not cur or n >= 60:
                break
        print(a[1], "pages", n, "rows", rows, "COMPLETE" if not cur else "TRUNCATED")
