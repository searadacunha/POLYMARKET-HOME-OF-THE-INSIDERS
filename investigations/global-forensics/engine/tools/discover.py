"""From each catalogue market's tape to the accounts worth reading, winners and losers alike, with no outcome in the selection.

For each market: entrant buyers of EITHER token before the public event, largest first, N per token. Only their timing, size and price choose them.
Writes results/discovery/<market>.json and a wallet list for run_wallets.py. No account is called an insider: this is a reading list.
"""
import gzip
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env

ROOT = env.data_root()
PER_TOKEN = 30
LOOKBACK = 8 * 86400
WINDOWS = (5, 30, 90, 300, 900, 3600)
SECONDS = lambda s: int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())


def main(markets_file, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    wallet_list = {}
    for m in json.loads(Path(markets_file).read_text()):
        path = ROOT / 'markets' / m['id'] / 'tape.jsonl.gz'
        event = SECONDS(m['event_utc'])
        with gzip.open(path, 'rt') as f:
            rows = sorted((json.loads(l) for l in f), key=lambda r: r['timestamp'])
        seen, entrants = set(), []
        for r in rows:
            w = r['proxy_wallet'].lower()
            if w not in seen and r['side'] == 'BUY' and r['timestamp'] < event:
                entrants.append(dict(wallet=w, token=r['token_id'], outcome=r.get('outcome'), ts=r['timestamp'], price=r['price'], usd=round(float(r['size']) * float(r['price']), 2), seconds_before_event=event - r['timestamp'], tx=r['transaction_hash']))
            seen.add(w)
        by_token = defaultdict(list)
        for e in entrants:
            by_token[e['token']].append(e)
        chosen = []
        groups = {}
        for token, items in by_token.items():
            items.sort(key=lambda x: x['ts'])
            for w in WINDOWS:
                best = 0
                left = 0
                for i, e in enumerate(items):
                    while items[left]['ts'] <= e['ts'] - w:
                        left += 1
                    best = max(best, len({x['wallet'] for x in items[left:i + 1]}))
                groups.setdefault(token, {})[w] = best
            chosen += sorted(items, key=lambda x: -x['usd'])[:PER_TOKEN]
        result = dict(market=m['id'], question=m['question'], event_utc=m['event_utc'], event_time_basis=m['event_time_basis'], selection=m['selection'], status=m['status'], reports=m['reports'], rows=len(rows), entrants=len(entrants), largest_group_of_entrants_by_window=groups, chosen=chosen, chosen_rule=f'{PER_TOKEN} largest entrant buyers per token before the event, both tokens, outcome unused', not_an_accusation=True)
        (out_dir / f"{m['id']}.json").write_text(json.dumps(result, indent=0))
        for e in chosen:
            wallet_list.setdefault(e['wallet'], dict(slug='d-' + e['wallet'][:12], wallet=e['wallet'], group='discovery', markets=[]))['markets'].append(m['id'])
        print(m['id'], 'rows', len(rows), 'entrants', len(entrants), 'chosen', len(chosen), flush=True)
    (out_dir / 'wallets.json').write_text(json.dumps(sorted(wallet_list.values(), key=lambda x: x['wallet']), indent=0))
    print('wallets', len(wallet_list))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
