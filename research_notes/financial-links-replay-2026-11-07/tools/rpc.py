"""Minimal JSON-RPC helper with retries for free Polygon/Ethereum endpoints (drpc returns null from lagging nodes)."""
import json, time, urllib.request
ENDPOINTS = {'polygon': ['https://polygon.drpc.org'], 'ethereum': ['https://eth.drpc.org', 'https://ethereum-rpc.publicnode.com']}
def call(chain, method, params, tries=6):
    last = None
    for i in range(tries):
        url = ENDPOINTS[chain][i % len(ENDPOINTS[chain])]
        try:
            req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                         headers={'content-type': 'application/json', 'user-agent': 'forensic-replay/1.0'})
            r = json.load(urllib.request.urlopen(req, timeout=40))
            if r.get('result') is not None:
                return r['result']
            last = r
        except Exception as e:
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f'{chain} {method} {params}: {last}')
