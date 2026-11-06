"""Sequential collector for the Inca cross-check. One network worker per process; run at most two processes.

Every response is archived raw outside git with a meta file (no key) and its SHA-256. An HTTP error,
a malformed page or an empty page that announces more stops the run: an error is never read as an empty list.

Usage (RAW defaults to ~/Projects/Polymarket-inca-raw-20261106/raw):
  python3 -I collect.py pm <address>...          Polymarket v2 activity (all pages) and public profile (closed-positions v1 is retired, HTTP 410)
  python3 -I collect.py relay <address>...       Relay requests/v2?user= (all pages)
  python3 -I collect.py es <action> <address>... Etherscan v2 on Polygon (tokentx, txlist, txlistinternal)
  python3 -I collect.py rcpt <hash>...           Polygon receipt and transaction (public RPC)
  python3 -I collect.py labels <name> <chain> <address>...   Blockscout metadata labels
  python3 -I collect.py http <name> <url>
"""
import hashlib, json, os, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(os.environ.get("INCA_RAW", Path.home() / "Projects/Polymarket-inca-raw-20261106/raw"))
UA = "inca-crosscheck-research/1.0"
RPCS = ["https://polygon.drpc.org", "https://polygon-rpc.com", "https://polygon-bor-rpc.publicnode.com"]
STATS = {"requests": 0, "ok": 0, "retried": 0}


def archive(path: Path, body: bytes, meta: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    meta = {**meta, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body),
            "fetched_utc": datetime.now(timezone.utc).isoformat()}
    path.with_name(path.name[:-5] + ".meta.json").write_text(json.dumps(meta, indent=1))


def fetch(url, data=None, headers=None, tries=7):
    """Returns (status, body). Retries 429, 5xx and network errors; any other HTTP error is returned to the caller."""
    h = {"user-agent": UA, "accept": "application/json", **(headers or {})}
    delay = 2.0
    for i in range(tries):
        STATS["requests"] += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=90) as r:
                body = r.read()
            json.loads(body)  # truncated JSON is retried, never archived as a result
            STATS["ok"] += 1
            return r.status, body
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                STATS["retried"] += 1; time.sleep(delay); delay = min(delay * 2, 90); continue
            return e.code, e.read()
        except Exception:
            STATS["retried"] += 1; time.sleep(delay); delay = min(delay * 2, 90); continue
    raise SystemExit(f"{url.split('apikey=')[0]}: failed after {tries} tries")


def get(path: Path, url, shown=None, delay=0.4):
    if path.exists():
        return json.loads(path.read_bytes())
    st, body = fetch(url)
    if st != 200:
        archive(path.with_name(path.stem + f".HTTP{st}.json"), body, {"url": shown or url, "http_status": st})
        return None
    archive(path, body, {"url": shown or url, "http_status": st})
    time.sleep(delay)
    return json.loads(body)


def pm(addr):
    d = RAW / "polymarket" / addr
    cur, n, rows = None, 0, 0
    while True:
        u = (f"https://data-api.polymarket.com/v2/activity?user={addr}&limit=500&sort_by=TIMESTAMP"
             f"&sort_direction=ASC&exclude_deposits_withdrawals=false" + (f"&cursor={cur}" if cur else ""))
        b = get(d / f"v2activity_p{n:03d}.json", u)
        if b is None or not isinstance(b.get("data"), list) or "pagination" not in b:
            raise SystemExit(f"{addr}: malformed activity page {n}")
        cur = b["pagination"].get("next_cursor")
        if not b["data"] and cur:
            raise SystemExit(f"{addr}: empty activity page {n} announcing more")
        rows += len(b["data"]); n += 1
        if not cur:
            break
        if n >= 200:
            raise SystemExit(f"{addr}: more than 200 activity pages")
    get(d / "profile.json", f"https://gamma-api.polymarket.com/public-profile?address={addr}")
    (d / "DONE.json").write_text(json.dumps({"activity_pages": n, "activity_rows": rows, "termination": "END"}))
    print(addr, "activity", rows)


def pmdw(addr):
    """DEPOSIT and WITHDRAWAL rows only (PLAN_CONTROLS.md amendment A1), every page."""
    d = RAW / "polymarket_dw" / addr
    cur, n, rows = None, 0, 0
    while True:
        u = (f"https://data-api.polymarket.com/v2/activity?user={addr}&limit=500&sort_by=TIMESTAMP&sort_direction=ASC"
             f"&exclude_deposits_withdrawals=false&type=DEPOSIT,WITHDRAWAL" + (f"&cursor={cur}" if cur else ""))
        b = get(d / f"p{n:03d}.json", u)
        if b is None or not isinstance(b.get("data"), list) or "pagination" not in b:
            raise SystemExit(f"{addr}: malformed activity page {n}")
        if any(r.get("type") not in ("DEPOSIT", "WITHDRAWAL") for r in b["data"]):
            raise SystemExit(f"{addr}: the type filter was not applied on page {n}")
        cur = b["pagination"].get("next_cursor")
        if not b["data"] and cur:
            raise SystemExit(f"{addr}: empty activity page {n} announcing more")
        rows += len(b["data"]); n += 1
        if not cur:
            break
        if n >= 200:
            raise SystemExit(f"{addr}: more than 200 pages of deposits and withdrawals")
    (d / "DONE.json").write_text(json.dumps({"pages": n, "rows": rows, "termination": "END"}))
    print(addr, "deposits+withdrawals", rows, flush=True)


def relay(addr):
    d = RAW / "relay" / addr
    cont, n, total = None, 0, 0
    while True:
        u = f"https://api.relay.link/requests/v2?user={addr}&limit=50" + (f"&continuation={cont}" if cont else "")
        b = get(d / f"p{n:03d}.json", u, delay=13)
        if b is None or not isinstance(b.get("requests"), list):
            raise SystemExit(f"{addr}: malformed Relay page {n}")
        cont = b.get("continuation")
        if not b["requests"] and cont:
            raise SystemExit(f"{addr}: empty Relay page {n} with continuation")
        total += len(b["requests"]); n += 1
        if not cont:
            break
        if n >= 100:
            raise SystemExit(f"{addr}: more than 100 Relay pages")
    (d / "DONE.json").write_text(json.dumps({"pages": n, "requests": total, "termination": "END"}))
    print(addr, "relay", total)


def tape(cond):
    """Whole /v2/trades tape of one market, newest first (the endpoint ignores start and end)."""
    d = RAW / "trades" / cond
    cur, n, rows, prev_min = None, 0, 0, None
    while True:
        u = (f"https://data-api.polymarket.com/v2/trades?condition={cond}&limit=1000&taker_only=false"
             + (f"&cursor={cur}" if cur else ""))
        b = get(d / f"p{n:04d}.json", u, delay=10)
        if b is None or not isinstance(b.get("data"), list) or not isinstance(b.get("pagination"), dict):
            raise SystemExit(f"{cond}: malformed trades page {n}")
        data, cur = b["data"], b["pagination"].get("next_cursor")
        if not data and cur:
            raise SystemExit(f"{cond}: empty trades page {n} announcing more")
        if data:
            ts = [int(x["timestamp"]) for x in data]
            if prev_min is not None and max(ts) > prev_min:
                raise SystemExit(f"{cond}: page {n} is newer than the previous page")
            prev_min = min(ts)
        rows += len(data); n += 1
        if not cur or not b["pagination"].get("has_more", True):
            break
        if n >= 400:
            raise SystemExit(f"{cond}: more than 400 trades pages")
    (d / "DONE.json").write_text(json.dumps({"pages": n, "rows": rows, "oldest": prev_min, "termination": "END"}))
    print(cond, "pages", n, "rows", rows)


def es(action, addr, max_pages=10):
    key = next(l.split("=", 1)[1].strip().strip("\"'") for l in (Path.home() / "Downloads/.env").read_text().splitlines()
               if l.startswith("ETHERSCAN_API_KEY="))
    d, page, rows = RAW / "etherscan" / addr, 1, 0
    while True:
        out = d / f"137_{action}_p{page}.json"
        q = f"chainid=137&module=account&action={action}&address={addr}&page={page}&offset=1000&sort=asc"
        if out.exists():
            res = json.loads(out.read_bytes())["result"]
        else:
            for i in range(8):
                st, body = fetch(f"https://api.etherscan.io/v2/api?{q}&apikey={key}")
                b = json.loads(body)
                if st == 200 and (b.get("status") == "1" or "No transactions found" in str(b.get("message"))):
                    break
                time.sleep(3 * (i + 1))  # "too busy" or rate limit: never taken for an empty list
            else:
                raise SystemExit(f"etherscan {action} {addr}: {str(b)[:200]}")
            archive(out, body, {"url": f"https://api.etherscan.io/v2/api?{q}&apikey=<KEY>", "status": b.get("status")})
            res = b.get("result") or []
            time.sleep(0.35)
        if not isinstance(res, list):
            raise SystemExit(f"etherscan {action} {addr}: result is not a list")
        rows += len(res)
        if len(res) < 1000:
            break
        if page >= max_pages:  # Etherscan caps page*offset at 10,000 rows; a capped read is recorded, never silent
            (d / f"137_{action}_CAPPED.json").write_text(json.dumps({"pages": page, "rows": rows, "termination": "MAX_PAGES"}))
            print(action, addr, rows, "MAX_PAGES"); return
        page += 1
    (d / f"137_{action}_DONE.json").write_text(json.dumps({"pages": page, "rows": rows, "termination": "END"}))
    print(action, addr, rows)


def rcpt(h):
    for m in ("eth_getTransactionReceipt", "eth_getTransactionByHash"):
        out = RAW / "polygon" / f"{h}.{m}.json"
        if out.exists():
            continue
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": [h]}).encode()
        for ep in RPCS * 2:
            st, raw = fetch(ep, data=body, headers={"content-type": "application/json"})
            if st == 200 and json.loads(raw).get("result"):
                archive(out, raw, {"endpoint": ep, "method": m, "params": [h], "http_status": st})
                break
            time.sleep(1)
        else:
            raise SystemExit(f"{h} {m}: empty or refused on every node")
        time.sleep(0.25)


def code(addrs):
    """eth_getCode at latest on Polygon, one archived answer per address (PLAN_CONTROLS.md service rule)."""
    for a in addrs:
        out = RAW / "polygon_code" / f"{a}.json"
        if out.exists():
            continue
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getCode", "params": [a, "latest"]}).encode()
        for ep in RPCS * 2:
            st, raw = fetch(ep, data=body, headers={"content-type": "application/json"})
            if st == 200 and isinstance(json.loads(raw).get("result"), str):
                archive(out, raw, {"endpoint": ep, "method": "eth_getCode", "params": [a, "latest"], "http_status": st})
                break
            time.sleep(1)
        else:
            raise SystemExit(f"{a} eth_getCode: refused on every node")
        time.sleep(0.2)


def labels(name, chain, addrs):
    for i in range(0, len(addrs), 20):
        part = ",".join(addrs[i:i + 20])
        get(RAW / "blockscout" / f"{name}_{chain}_{i // 20}.json",
            f"https://metadata.services.blockscout.com/api/v1/metadata?chainId={chain}&addresses={part}&tagsLimit=20")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "pm":
        [pm(x.lower()) for x in a[1:]]
    elif a[0] == "pmdw":
        [pmdw(x.lower()) for x in a[1:]]
    elif a[0] == "relay":
        [relay(x.lower()) for x in a[1:]]
    elif a[0] == "tape":
        tape(a[1].lower())
    elif a[0] == "es":  # es <action> [--max-pages N] <address>...
        mp = int(a[3]) if a[2] == "--max-pages" else 10
        [es(a[1], x.lower(), mp) for x in (a[4:] if a[2] == "--max-pages" else a[2:])]
    elif a[0] == "rcpt":
        [rcpt(x.lower()) for x in a[1:]]
    elif a[0] == "code":
        code([x.lower() for x in a[1:]])
    elif a[0] == "labels":
        labels(a[1], a[2], [x.lower() for x in a[3:]])
    elif a[0] == "http":
        get(RAW / "http" / f"{a[1]}.json", a[2])
    print("stats", json.dumps(STATS), file=sys.stderr)
