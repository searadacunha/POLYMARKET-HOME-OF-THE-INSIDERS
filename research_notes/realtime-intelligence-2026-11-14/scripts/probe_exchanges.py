"""Which contracts emit OrderFilled right now, and what ExchangeV3 carries. Public Polygon nodes, about ten requests.

    python3 -I scripts/probe_exchanges.py > data/exchange_probe_YYYYMMDD.json

Network read, not run by the checks of the repository: the file kept in data/ is the reading of 14 November 2026."""
import collections, gzip, json, sys, time, urllib.request

ORDER_FILLED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
NAMES = {"0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange", "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange",
         "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "ExchangeV3 (Polymarket Protocol V2)",
         "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e": "earlier CTF Exchange", "0xc5d563a36ae78145c45a50134d48a1215220f80a": "earlier Neg Risk CTF Exchange"}
RPC = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"]


def rpc(method, params):
    last = None
    for url in RPC:
        try:
            req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read()
                raw = gzip.decompress(raw) if r.headers.get("Content-Encoding") == "gzip" else raw
            j = json.loads(raw)
            if "error" in j:
                last = str(j["error"])[:160]; continue
            return j["result"], url.split("/")[2]
        except Exception as e:                      # the next endpoint is tried; the last error is raised if none answers
            last = repr(e)[:160]
        time.sleep(0.5)
    raise RuntimeError(last)


def main():
    head = int(rpc("eth_blockNumber", [])[0], 16) - 5
    span = 150
    logs, node = [], None
    for lo in range(head - span + 1, head + 1, 50):          # by event signature only, no contract named
        part, node = rpc("eth_getLogs", [{"fromBlock": hex(lo), "toBlock": hex(min(head, lo + 49)), "topics": [ORDER_FILLED]}])
        logs += part; time.sleep(0.6)
    by = collections.Counter(l["address"].lower() for l in logs)
    modules = collections.Counter()
    for l in logs:
        if l["address"].lower() == "0xe3333700ca9d93003f00f0f71f8515005f6c00aa":
            modules[int(l["data"][2 + 64:2 + 128], 16) >> 248] += 1
    old = {}
    for a in ("0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e", "0xc5d563a36ae78145c45a50134d48a1215220f80a"):
        part, _ = rpc("eth_getLogs", [{"fromBlock": hex(head - 1999), "toBlock": hex(head), "address": a}])
        old[NAMES[a]] = dict(collections.Counter(l["topics"][0][:18] for l in part)); time.sleep(0.6)
    out = {"read_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "node": node, "blocks": [head - span + 1, head],
           "order_filled_logs": len(logs), "emitters": {NAMES.get(a, a): n for a, n in by.most_common()},
           "emitters_outside_the_three_exchanges": {a: n for a, n in by.items() if a not in list(NAMES)[:3]},
           "exchange_v3_share": round(by.get("0xe3333700ca9d93003f00f0f71f8515005f6c00aa", 0) / max(1, len(logs)), 4),
           "exchange_v3_fills_by_module": {{1: "binary", 2: "negative risk", 3: "combinatorial"}.get(m, str(m)): n for m, n in modules.items()},
           "earlier_exchanges_logs_last_2000_blocks_by_topic": old,
           "registry": NAMES,
           "note": "module = top byte of the position identifier carried by the fill (docs.polymarket.com/resources/onchain-position-data)"}
    json.dump(out, sys.stdout, indent=1); print()


if __name__ == "__main__":
    main()
