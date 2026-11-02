"""Part B, E6. Gap between funding and first family buy, and exit timing, for named wallets and comparators. Public activity only; aliases never kept."""
import gzip
import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import rows as R
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = Path(ETUDE)
labels = json.loads((E / 'data/labels_retro.json').read_text())
SEED = 20261101
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t)) if t else None
fam = [r for r in R.family() if r[0] == 'M' and r[4] == 'BUY']
spent = defaultdict(lambda: defaultdict(float))
first_buy = {}
for r in fam:
    spent[r[2]][r[3]] += r[5]
    first_buy[r[3]] = min(first_buy.get(r[3], r[8]), r[8])
named = set(labels['named'].values())
same = sorted(w for w, x in spent[labels['token_same']].items() if x >= 1000 and w not in named)
opposite = sorted(w for w, x in spent[labels['token_opposite']].items() if x >= 1000 and w not in named)
groups = dict(named=sorted(named), non_surlignes=sorted(labels['not_highlighted'].values()), meme_token=same, token_oppose=opposite)


def history(wallet):
    rows, cursor = [], None
    for _ in range(12):
        params = dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        body = net.get('https://data-api.polymarket.com/v2/activity', params)
        if not isinstance(body, dict) or '_http_error' in body:
            raise RuntimeError(f'{wallet}: {body}')
        rows += [dict(t=r['timestamp'], k=r['type'], usd=r.get('usdc_size')) for r in body.get('data', [])]
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows, True
    return rows, False


per = {}
errors = 0
for name, wallets in groups.items():
    for w in wallets:
        if w in per:
            continue
        rows, complete = history(w)
        deposits = [r for r in rows if r['k'] == 'DEPOSIT']
        fb = first_buy.get(w)
        before = [r for r in deposits if fb and r['t'] <= fb]
        out = [r for r in rows if r['k'] == 'WITHDRAWAL']
        per[w] = dict(complete=complete, first_family_buy=fb, deposits=len(deposits), first_event=rows[0]['t'] if rows else None, last_deposit_before=before[-1]['t'] if before else None, gap_s=fb - before[-1]['t'] if before else None, first_deposit_to_buy_s=fb - deposits[0]['t'] if deposits and fb else None, withdrawals=len(out), first_withdrawal=out[0]['t'] if out else None, usd_out=round(sum(float(r['usd'] or 0) for r in out), 2), rows=len(rows))


def median(v):
    v = sorted(x for x in v if x is not None)
    return None if not v else v[len(v) // 2]


summary = {}
for name, wallets in groups.items():
    gaps = [per[w]['gap_s'] for w in wallets]
    fw = [per[w]['first_withdrawal'] for w in wallets]
    summary[name] = dict(wallets=len(wallets), median_gap_min=round(median(gaps) / 60, 1) if median(gaps) is not None else None, gap_under_1h=sum(1 for g in gaps if g is not None and g <= 3600), no_deposit_seen=sum(1 for g in gaps if g is None), with_withdrawal=sum(1 for x in fw if x), median_first_withdrawal=UTC(median(fw)), one_withdrawal_or_more_before_ceremony=sum(1 for x in fw if x and x < 1793131200))
(E / 'derived/B_E6.json').write_text(json.dumps(dict(groups=groups, per_wallet=per, summary=summary), indent=0))
enregistrer(ETUDE, 'E6_funding', True, len(per), 'claude', n_effectif=1, n_comparaisons=len(summary) * 3, sortie='derived/B_E6.json')
print(json.dumps(summary, indent=0))
