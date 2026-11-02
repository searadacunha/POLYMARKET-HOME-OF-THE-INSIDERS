"""Public activity of trading accounts, one summary line per account: deposits, first trade, positions by market and outcome. Same reader for matched accounts and for witnesses. Pages capped, the cap is written. Usage: pm_activity.py <input csv with column account> <output jsonl>. Resumes."""
import csv, json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
URL = 'https://data-api.polymarket.com/v2/activity'
MAX_PAGES = 12


def read(acct):
    rows, cursor, pages = [], None, 0
    while pages < MAX_PAGES:
        p = dict(user=acct, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            p['cursor'] = cursor
        body = net.get(URL, p, pause=.25, store=False, accept=())
        if not isinstance(body, dict) or 'data' not in body:
            raise RuntimeError(f'{acct}: {str(body)[:160]}')
        rows += body['data']
        pages += 1
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows, True
    return rows, False


def summary(acct, rows, complete):
    types = defaultdict(int)
    pos = {}
    dep, wd = [], []
    trades = []
    for x in rows:
        t = x.get('type')
        types[t] += 1
        ts = int(x.get('timestamp') or 0)
        usd = float(x.get('usdc_size') or x.get('usdcSize') or 0)
        if t == 'DEPOSIT':
            dep.append((ts, usd, x.get('transaction_hash') or x.get('transactionHash')))
        elif t == 'WITHDRAWAL':
            wd.append((ts, usd, x.get('transaction_hash') or x.get('transactionHash')))
        elif t == 'TRADE':
            cond, oc = x.get('condition_id') or x.get('conditionId'), x.get('outcome')
            k = f'{cond}|{oc}'
            v = pos.setdefault(k, dict(title=x.get('title'), first=ts, buy=0.0, sell=0.0, n=0))
            v['n'] += 1
            v['first'] = min(v['first'], ts)
            v['buy' if x.get('side') == 'BUY' else 'sell'] += usd
            trades.append(ts)
    trades.sort()
    return dict(account=acct, complete=complete, rows=len(rows), types=dict(types), first_deposit=dep[0] if dep else None, n_deposits=len(dep), deposit_usd=round(sum(d[1] for d in dep), 2), withdraw_usd=round(sum(d[1] for d in wd), 2), first_trade=trades[0] if trades else None, last_trade=trades[-1] if trades else None, n_trades=len(trades), positions=pos)


if __name__ == '__main__':
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    done = set()
    if out.exists():
        done = {json.loads(l)['account'] for l in out.open()}
    todo = [r['account'] for r in csv.DictReader(open(src))]
    todo = [a for a in dict.fromkeys(todo) if a not in done]
    print('to read', len(todo), 'done', len(done), flush=True)
    with out.open('a') as f:
        for i, a in enumerate(todo):
            rows, complete = read(a)
            f.write(json.dumps(summary(a, rows, complete)) + '\n')
            f.flush()
            if i % 50 == 0:
                print(i, a[:10], len(rows), flush=True)
    print('done')
