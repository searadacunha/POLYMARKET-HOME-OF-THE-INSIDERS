#!/usr/bin/env python3
"""
Chain data toolkit (Polygon) — Etherscan V2 unified API + Polygon RPC.
The proxy-unwind primitive lives here: txlistinternal_by_txhash().
Reads ETHERSCAN_API_KEY / ETHERSCAN_BASE_URL / POLYGON_RPC_URL from ~/Downloads/.env.
"""
import os, json, time, urllib.request, urllib.parse, urllib.error

ENV_PATH = os.path.expanduser("~/Downloads/.env")

def _env():
    cfg = {}
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return cfg

_CFG = _env()
ETHERSCAN_KEY = os.environ.get("ETHERSCAN_API_KEY") or _CFG.get("ETHERSCAN_API_KEY")
# V2 unified base; allow override from .env, default to canonical V2 endpoint
_BASE = _CFG.get("ETHERSCAN_BASE_URL") or "https://api.etherscan.io/v2/api"
if "/v2/" not in _BASE:
    # if .env still holds a V1 base, coerce to V2
    _BASE = "https://api.etherscan.io/v2/api"
# CN/PM forensics live on Polygon — force 137 (ignore ETHERSCAN_CHAIN_ID=1 default in .env)
CHAIN_ID = "137"
POLYGON_RPC = os.environ.get("POLYGON_RPC_URL") or _CFG.get("POLYGON_RPC_URL")

import threading
_last_call = [0.0]
_throttle_lock = threading.Lock()
def _throttle(min_interval=0.22):
    with _throttle_lock:
        dt = time.time() - _last_call[0]
        if dt < min_interval:
            time.sleep(min_interval - dt)
        _last_call[0] = time.time()

def es(params, retries=4):
    """Call Etherscan V2 with chainid + apikey. Returns the 'result' field."""
    q = dict(params)
    q["chainid"] = CHAIN_ID
    q["apikey"] = ETHERSCAN_KEY
    url = _BASE + "?" + urllib.parse.urlencode(q)
    last = None
    for attempt in range(retries):
        _throttle()
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                obj = json.loads(r.read().decode())
            # status "0" with "No transactions found" is a valid empty result
            if obj.get("status") == "1":
                return obj.get("result", [])
            msg = obj.get("message", "")
            res = obj.get("result", "")
            if isinstance(res, list):
                return res
            if "No transactions found" in msg or "No records found" in str(res):
                return []
            if "rate limit" in str(res).lower() or "Max calls" in str(res):
                last = res; time.sleep(1.0 + attempt); continue
            return res  # NOTOK message string
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = repr(e); time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"etherscan failed: {last}")

def txlist(address, startblock=0, endblock=99999999, sort="asc", offset=10000, page=1):
    return es({"module":"account","action":"txlist","address":address,
               "startblock":startblock,"endblock":endblock,"sort":sort,
               "offset":offset,"page":page})

def txlistinternal_by_addr(address, startblock=0, endblock=99999999, sort="asc", offset=10000, page=1):
    return es({"module":"account","action":"txlistinternal","address":address,
               "startblock":startblock,"endblock":endblock,"sort":sort,
               "offset":offset,"page":page})

def txlistinternal_by_txhash(txhash):
    """PROXY-UNWIND PRIMITIVE: internal value transfers inside one tx."""
    return es({"module":"account","action":"txlistinternal","txhash":txhash})

def tokentx(address, contractaddress=None, startblock=0, endblock=99999999, sort="asc", offset=10000, page=1):
    p = {"module":"account","action":"tokentx","address":address,
         "startblock":startblock,"endblock":endblock,"sort":sort,"offset":offset,"page":page}
    if contractaddress:
        p["contractaddress"] = contractaddress
    return es(p)

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
def get_receipt(txhash):
    """Receipt via Etherscan V2 proxy module (same working key); fallback to raw RPC."""
    r = es({"module":"proxy","action":"eth_getTransactionReceipt","txhash":txhash})
    if isinstance(r, dict) and r.get("logs") is not None:
        return r
    try:
        return rpc("eth_getTransactionReceipt", [txhash])
    except Exception:
        return None

def erc20_transfers_in_tx(txhash):
    """TRUE per-tx ERC-20 proxy-unwind: decode every Transfer event in the receipt
    (includes router-internal hops). Returns [{token,from,to,value_raw}]."""
    rc = get_receipt(txhash)
    out = []
    if not rc:
        return out
    for log in rc.get("logs", []):
        topics = log.get("topics", [])
        if len(topics) >= 3 and topics[0].lower() == TRANSFER_TOPIC:
            frm = "0x" + topics[1][-40:]
            to = "0x" + topics[2][-40:]
            data = log.get("data", "0x")
            val = int(data, 16) if data not in ("0x", "") else 0
            out.append({"token": log.get("address","").lower(),
                        "from": frm.lower(), "to": to.lower(), "value_raw": val})
    return out

_code_cache = {}
def is_contract(addr):
    """True if addr has bytecode (contract). Via Etherscan proxy eth_getCode."""
    a = addr.lower()
    if a in _code_cache:
        return _code_cache[a]
    code = es({"module":"proxy","action":"eth_getCode","address":a,"tag":"latest"})
    val = isinstance(code, str) and code not in ("0x", "0x0", "", None) and len(code) > 2
    _code_cache[a] = val
    return val

def gas_funders(wallet):
    """Who sent native MATIC TO this wallet (gas). Returns [{from,value_matic,hash,ts}].
    Combines external txlist (value>0, to=wallet) and internal native transfers."""
    out = []
    for t in txlist(wallet, sort="asc"):
        if isinstance(t, dict) and t.get("to","").lower()==wallet.lower() and int(t.get("value","0"))>0:
            out.append({"from":t["from"].lower(),"value_matic":int(t["value"])/1e18,
                        "hash":t["hash"],"ts":int(t["timeStamp"]),"kind":"ext"})
    for t in txlistinternal_by_addr(wallet, sort="asc"):
        if isinstance(t, dict) and t.get("to","").lower()==wallet.lower() and int(t.get("value","0"))>0:
            out.append({"from":t["from"].lower(),"value_matic":int(t["value"])/1e18,
                        "hash":t["hash"],"ts":int(t["timeStamp"]),"kind":"int"})
    return out

def classify_funder(addr, sample_window=10000):
    """A CN gaser sends ONLY gas (tiny native), never ERC-20 capital. Returns
    {sent_capital_tx, sent_gas_tx, max_native_out, verdict}."""
    cap = 0
    for t in tokentx(addr, sort="desc", offset=200, page=1):
        if isinstance(t, dict) and t.get("from","").lower()==addr.lower():
            cap += 1
    gas_tx, maxnat = 0, 0.0
    for t in txlistinternal_by_addr(addr, sort="desc", offset=200, page=1):
        if isinstance(t, dict) and t.get("from","").lower()==addr.lower() and int(t.get("value","0"))>0:
            gas_tx += 1; maxnat = max(maxnat, int(t["value"])/1e18)
    verdict = "GASER_PURE" if (cap==0 and gas_tx>0 and maxnat<=0.5) else ("MIXED_HAS_CAPITAL" if cap>0 else "OTHER")
    return {"sent_capital_tx":cap,"sent_gas_tx":gas_tx,"max_native_out":maxnat,"verdict":verdict}

def rpc(method, params, retries=3):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(POLYGON_RPC, data=body, method="POST",
                                         headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode()).get("result")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = repr(e); time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"rpc failed: {last}")

if __name__ == "__main__":
    import sys
    F2020 = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"
    print(f"BASE={_BASE} CHAIN={CHAIN_ID} key_set={bool(ETHERSCAN_KEY)} rpc_set={bool(POLYGON_RPC)}")
    print("=== f2020 token transfers (latest 5, USDC.e) ===")
    USDCe = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
    tt = tokentx(F2020, contractaddress=USDCe, sort="desc", offset=5, page=1)
    if isinstance(tt, list):
        for t in tt[:5]:
            v = int(t["value"])/1e6
            print(f"  blk {t['blockNumber']} {t['hash'][:14]} from {t['from'][:10]} -> {t['to'][:10]} ${v:,.2f}")
    else:
        print("  ->", tt)
    print("=== proxy-unwind self-test: internal txns of f2020's latest outgoing tx ===")
    if isinstance(tt, list) and tt:
        h = tt[0]["hash"]
        itx = txlistinternal_by_txhash(h)
        print(f"  tx {h[:16]} internal legs: {len(itx) if isinstance(itx,list) else itx}")
        if isinstance(itx, list):
            for i in itx[:6]:
                print(f"    {i.get('from','')[:10]} -> {i.get('to','')[:10]} val {int(i.get('value','0'))/1e18:.6f} type={i.get('type')}")
