"""How common is each funding route among wallets nobody named? Same hop reader on comparators, so a shared exchange or a Solana route can be read against a base rate.

Control groups:
- non_surlignes, meme_token, token_oppose: from collective/derived/B_E6.json.
- fraiches_recensement: wallets with a first event since 1 Oct and at least 5,000 $ of census buys outside the Ballon d'Or family, 40 drawn with a fixed seed.

Each wallet: the deposit nearest before its first family buy, or its first deposit in the census group. Named wallets are read the same way. Checkpoint per wallet.
"""
import gzip
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'collective/code'))
import case_chain as C
import net
import rows as R

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'controls/funding_baseline.jsonl'
SEED = 20261101
OCT1 = 1790812800


def census_fresh(n=40):
    ages = {}
    with gzip.open(ROOT / 'collective/data/ages.jsonl.gz', 'rt') as f:
        for line in f:
            a = json.loads(line)
            if 'first_ts' in a:
                ages[a['wallet']] = a['first_ts']
    family = {r[3] for r in R.family()}
    spent = defaultdict(float)
    for r in R.census({}):
        if r[4] == 'BUY':
            spent[r[3]] += r[5]
    pool = sorted(w for w, x in spent.items() if x >= 5000 and w in ages and ages[w] >= OCT1 and w not in family)
    random.Random(SEED).shuffle(pool)
    return pool[:n], len(pool)


def history(wallet):
    rows, cursor = [], None
    for _ in range(12):
        params = dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        body = net.get('https://data-api.polymarket.com/v2/activity', params)
        if not isinstance(body, dict) or '_http_error' in body:
            raise RuntimeError(f'{wallet}: {body}')
        rows += body.get('data', [])
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows
    return rows


def summarise(hop, relations):
    labels = sorted(({(r.get('source_label') or {}).get('name') for r in relations if r.get('source_label')} | {(r.get('target_label') or {}).get('name') for r in relations if r.get('target_label')}) - {None})
    nonces = [int(r['basis'].split('nonce ')[1].split(',')[0]) for r in relations if 'nonce ' in (r.get('basis') or '')]
    record = (hop or {}).get('relay') or {}
    return dict(labels=[x for x in labels if x], immediate_kind=((hop or {}).get('kind') or {}).get('kind'), relay=bool(record), origin_chain=(record.get('in_txs') or [[None]])[0][0], relay_user_is_bridge=str(record.get('user', '')).lower() == (hop or {}).get('immediate_source'), high_nonce_sender=max(nonces, default=0) > 100000)


def main():
    OUT.parent.mkdir(exist_ok=True)
    done = set()
    if OUT.exists():
        done = {json.loads(l)['wallet'] for l in OUT.read_text().splitlines()}
    e6 = json.loads((ROOT / 'collective/derived/B_E6.json').read_text())
    fresh, pool = census_fresh()
    groups = dict(e6['groups'], fraiches_recensement=fresh)
    meta = dict(census_pool=pool, sampled=len(fresh), seed=SEED, read_at=time.time())
    (ROOT / 'controls/funding_baseline_meta.json').write_text(json.dumps(meta))
    first_buy = {w: p['first_family_buy'] for w, p in e6['per_wallet'].items()}
    for group, wallets in groups.items():
        for w in wallets:
            if w in done:
                continue
            row = dict(group=group, wallet=w)
            try:
                rows = history(w)
                deposits = [r for r in rows if r['type'] == 'DEPOSIT']
                fb = first_buy.get(w)
                before = [r for r in deposits if fb and r['timestamp'] <= fb]
                pick = before[-1] if before else (deposits[0] if deposits else None)
                if not pick:
                    row.update(state='NO_DEPOSIT_IN_HISTORY')
                else:
                    case = C.Case('baseline')
                    hop = C.trace_deposit(case, w, dict(tx=pick['transaction_hash'], at=pick['timestamp'], usd=pick['usdc_size']))
                    row.update(state='READ', deposit_tx=pick['transaction_hash'], usd=pick['usdc_size'], at=pick['timestamp'], **summarise(hop, case.relations))
            except (RuntimeError, KeyError, TypeError, ValueError, IndexError) as e:
                row.update(state='ERROR', error=str(e)[:200])
            with OUT.open('a') as f:
                f.write(json.dumps(row) + '\n')
            done.add(w)
            print(group, w[:10], row.get('state'), row.get('origin_chain'), row.get('labels'), flush=True)
    print('finished', net.Stats.calls)


if __name__ == '__main__':
    main()
