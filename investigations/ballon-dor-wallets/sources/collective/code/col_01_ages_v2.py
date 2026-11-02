"""First Polymarket event of each qualified wallet. Aliases are never written. An error is not an age and stops the run: re-running resumes from the cache."""
import gzip
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import rows as R
import signals as K

ETUDE = Path(__file__).resolve().parent.parent
CAP = 3200  # amendement 001


def wallets_reaching(all_rows, min_usd, hours=72):
    """Wallets reaching min_usd on one token within `hours`, any age, before T_FIN."""
    spent = defaultdict(list)
    for r in all_rows:
        if r[4] == 'BUY':
            spent[(r[3], r[2])].append((r[8], r[5]))
    out = set()
    for (w, _), v in spent.items():
        v.sort()
        a, s = 0, 0.0
        for t, x in v:
            s += x
            while v[a][0] <= t - hours * R.H:
                s -= v[a][1]
                a += 1
            if s >= min_usd:
                out.add(w)
                break
    return out


def census_prefilter(rows_g, min_wallets=3, min_usd=2500, hours=72):
    """Tokens with at least 3 wallets at min_usd within a window at some hourly tick; their wallets get an age."""
    by = K.by_token(rows_g)
    wanted = set()
    for token, rs in by.items():
        if len({w for _, w, _ in rs}) < min_wallets:
            continue
        for t in K.hourly_ticks(rs[0][0], rs[-1][0] + 72 * R.H):
            q = K.qualified(rs, t, hours, min_usd)
            if len(q) >= min_wallets:
                wanted.update(q)
    return wanted


fam = list(R.family())
ctl = list(R.controls())
family_tokens = {r[2]: r[0] for r in fam}
cat = R.catalog()
for tok, (event, _, _) in cat.items():
    if event in R.MEN:
        family_tokens.setdefault(tok, 'M')
    elif event in R.WOM:
        family_tokens.setdefault(tok, 'W')
cen = list(R.census(family_tokens))
first_stage = wallets_reaching(fam + ctl, 1000)
second_stage = census_prefilter(cen)
wanted = sorted(first_stage | second_stage)
counts = dict(first_stage=len(first_stage), census_prefilter=len(second_stage), wanted=len(wanted), cap=CAP, requested=0, returned=0, empty=0, errors=0)
if len(wanted) > CAP:
    raise SystemExit(f'{len(wanted)} wallets above the cap of {CAP}: amendment needed, nothing fetched')
out = ETUDE / 'data/ages.jsonl.gz'
ages = {}
for i, w in enumerate(wanted):
    counts['requested'] += 1
    page = net.get('https://data-api.polymarket.com/activity', dict(user=w, limit=1, sortBy='TIMESTAMP', sortDirection='ASC'), pause=.2)
    if not isinstance(page, list):
        counts['errors'] += 1
        ages[w] = dict(error=page.get('_http_error'))
    elif not page:
        counts['empty'] += 1
        ages[w] = dict(empty=True)
    else:
        counts['returned'] += 1
        ages[w] = dict(first_ts=page[0]['timestamp'], first_type=page[0]['type'])
    if i % 100 == 0:
        print(i, counts, flush=True)
with gzip.GzipFile(out, 'wb', mtime=0) as f:
    for w in wanted:
        f.write((json.dumps(dict(wallet=w, **ages[w]), sort_keys=True) + '\n').encode())
(ETUDE / 'data/ages_counts.json').write_text(json.dumps(counts, indent=1))
print(counts, 'http calls', net.Stats.calls, 'cached', net.Stats.cached)
