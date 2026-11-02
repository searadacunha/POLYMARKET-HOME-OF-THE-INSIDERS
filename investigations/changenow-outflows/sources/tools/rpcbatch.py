"""JSON-RPC batch for read-only calls. Any answer missing or in error raises: a partial batch never becomes an empty result. Guarded by net.guard."""
import json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net


def call(chain, calls, pause=.25, retries=5):
    """calls: list of (method, params). Returns results in order."""
    net.guard()
    for attempt in range(retries):
        for endpoint in net.RPC[chain]:
            time.sleep(pause * (1 + attempt))
            body = json.dumps([dict(jsonrpc='2.0', id=i, method=m, params=p) for i, (m, p) in enumerate(calls)]).encode()
            try:
                with urllib.request.urlopen(urllib.request.Request(endpoint, data=body, headers=net.UA), timeout=60) as r:
                    res = json.loads(r.read())
                by = {x['id']: x for x in res} if isinstance(res, list) else {}
                if len(by) == len(calls) and all('result' in x and not x.get('error') for x in by.values()):
                    net.note(kind='rpc_batch', chain=chain, n=len(calls), host=endpoint.split('/')[2], ok=True)
                    return [by[i]['result'] for i in range(len(calls))]
                net.note(kind='rpc_batch', chain=chain, n=len(calls), host=endpoint.split('/')[2], ok=False, sample=str(res)[:160])
            except Exception as e:
                net.note(kind='rpc_batch', chain=chain, n=len(calls), host=endpoint.split('/')[2], ok=False, error=type(e).__name__)
    raise RuntimeError(f'batch failed on every node: {calls[0][0]} x {len(calls)}')
