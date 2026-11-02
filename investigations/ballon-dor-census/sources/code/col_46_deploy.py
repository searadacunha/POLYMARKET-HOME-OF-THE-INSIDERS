"""On-chain deployment date of every wallet of the population and of every detector candidate: Etherscan getcontractcreation, 5 addresses per call.
Replaces join_date as the age of a wallet: it cannot change after the result and always precedes the wallet's first trade. An address with no record (an EOA trading directly) stays unknown, never fresh."""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

OUT = net.ROOT / 'derived/wallet_deploy.json'
MIN_ANY = 500.0


def wanted():
    """Every wallet with at least 500 $ of buys in the Ballon family, or in a control tape, before anything is read about its result."""
    totals = defaultdict(float)
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['side'] == 'BUY':
                totals[r['w']] += r['size'] * r['price']
    for p in (net.ROOT / 'derived/oos').glob('*.jsonl.gz'):
        with gzip.open(p, 'rt') as f:
            for line in f:
                r = json.loads(line)
                if r['side'] == 'BUY':
                    totals[r['w']] += r['size'] * r['price']
    return sorted(w for w, v in totals.items() if v >= MIN_ANY)


def main():
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in wanted() if w not in out]
    print('wallets', len(out) + len(todo), 'to read', len(todo), flush=True)
    for i in range(0, len(todo), 5):
        batch = todo[i:i + 5]
        d = net.get('https://api.etherscan.io/v2/api', dict(chainid=137, module='contract', action='getcontractcreation', contractaddresses=','.join(batch)), secret=dict(apikey=net.etherscan_key()))
        got = {r['contractAddress'].lower(): r for r in (d.get('result') or []) if isinstance(r, dict)}
        for w in batch:
            r = got.get(w)
            out[w] = dict(ts=int(r['timestamp']), block=int(r['blockNumber']), tx=r['txHash'], factory=(r.get('contractFactory') or '').lower()) if r and r.get('timestamp') else None
        if i % 500 == 0:
            OUT.write_text(json.dumps(out))
            print(i, 'with record', sum(1 for v in out.values() if v), flush=True)
    OUT.write_text(json.dumps(out))
    print('done', len(out), 'with record', sum(1 for v in out.values() if v), 'without', sum(1 for v in out.values() if not v))


if __name__ == '__main__':
    main()
