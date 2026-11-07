"""Market-level record of the KPMG cohort on earnings markets, rebuilt from Polymarket activity, Gamma resolutions and SEC records.
Auditor = firm signing the EX-23.1 (or sole EX-23/EX-15/EX-13) consent in the 2025-2026 annual filings (EDGAR full-text search).
Results time = SEC acceptance of the 8-K carrying Item 2.02 nearest the market's slug date (none for 6-K filers).
Usage: kpmg_markets.py RAW OUT_DIR"""
import json, glob, re, sys, csv, datetime, pathlib, math, itertools, random
RAW, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
ACC = {v['exact'][0]: k for k, v in json.load(open(RAW / 'profiles/resolution.json')).items()}
EXPANDED = {'perlgrow', 'boosthero', 'bostonguy'}
# Auditor overrides read from full-text hits outside EX-23/EX-15 (see sec/fts2_*): WFC EX-13 KPMG only, NKE 10-K PwC only, BNY EX-23.1 KPMG.
OVERRIDE = {'WFC': 'KPMG', 'NKE': 'PricewaterhouseCoopers', 'BK': 'KPMG'}
SEC = json.load(open(RAW / 'sec/sec_summary.json'))
BNY = json.load(open(RAW / 'sec/submissions_0001390777.json'))['filings']['recent']
SEC['BK']['current_reports'] = [{'accession': BNY['accessionNumber'][i], 'acceptance': BNY['acceptanceDateTime'][i], 'items': BNY['items'][i]}
                                for i in range(len(BNY['form'])) if BNY['form'][i] == '8-K']
def auditor(t):
    if t in OVERRIDE: return OVERRIDE[t]
    cf = SEC.get(t, {}).get('consent_firms', {})
    prim = [f for f, xs in cf.items() if any(x[0] in ('EX-23.1', 'EX-23', 'EX-23.01', 'EX-15.1', 'EX-15.3') for x in xs)]
    return prim[0] if len(prim) == 1 else ('AMBIGUOUS:' + '|'.join(sorted(cf)) if cf else 'UNRESOLVED')
GAM = {}
for f in glob.glob(str(RAW / 'gamma/markets_*.json')):
    if f.endswith('.meta'): continue
    for m in json.load(open(f)): GAM[m['conditionId']] = m
rows = []
for a, n in ACC.items():
    for f in sorted(glob.glob(str(RAW / f'xl/polymarket/{a}/v2activity_p*.json'))):
        if f.endswith('.meta.json'): continue
        rows += [dict(r, account=n) for r in json.load(open(f))['data'] if r['type'] in ('TRADE', 'REDEEM', 'MERGE', 'SPLIT')]
def utc(t): return datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
markets = {}
for r in rows:
    if r['type'] != 'TRADE': continue
    m = markets.setdefault(r['condition_id'], {'title': r['title'], 'slug': r['slug'], 'fills': []}); m['fills'].append(r)
out = []
for c, m in markets.items():
    g = GAM[c]; title = m['title']
    tk = re.search(r'\(([A-Z.]+)\)', title)
    is_earn = bool(tk) and ('earnings' in m['slug'] or 'Earnings' in title)
    if not is_earn: continue
    t = tk.group(1); aud = auditor(t)
    outcomes = json.loads(g['outcomes']); finals = [float(x) for x in json.loads(g['outcomePrices'])]
    winner = outcomes[finals.index(1.0)] if 1.0 in finals else None
    dm = re.search(r'-(\d\d)-(\d\d)-(20\d\d)(?:-|$)', m['slug'])
    sd = datetime.datetime(int(dm.group(3)), int(dm.group(1)), int(dm.group(2)), tzinfo=datetime.timezone.utc) if dm else None
    k8 = [datetime.datetime.fromisoformat(k['acceptance'].replace('Z', '+00:00')) for k in SEC.get(t, {}).get('current_reports', []) if '2.02' in (k['items'] or '')]
    k8 = [k for k in k8 if sd and -3 <= (k - sd).total_seconds() / 86400 <= 10]  # StoneX filed 6 days after the slug date
    filed = min(k8, key=lambda k: abs((k - sd).total_seconds())) if k8 else None
    closed = datetime.datetime.fromisoformat(g['closedTime'].replace(' ', 'T').replace('+00', '+00:00')) if g.get('closedTime') else None
    cutoff = filed or closed  # 6-K filers and the CarMax up/down market have no Item 2.02 stamp: position at market close
    for scope in ('core19', 'all22'):
        fl = [x for x in m['fills'] if scope == 'all22' or x['account'] not in EXPANDED]
        buys = [x for x in fl if x['side'] == 'BUY']
        if not buys: continue
        pre = [x for x in fl if x['timestamp'] < cutoff.timestamp()]
        net = {}
        for x in pre:
            k = (x['account'], x['outcome']); net[k] = net.get(k, 0.0) + (x['size'] if x['side'] == 'BUY' else -x['size'])
        held = {k: v for k, v in net.items() if v > 1.0}  # shares held at the cutoff, ignoring dust
        cost, acost = {}, {}
        for x in pre:
            if x['side'] == 'BUY' and (x['account'], x['outcome']) in held:
                c0 = cost.setdefault(x['outcome'], [0.0, 0.0]); c0[0] += x['usdc_size']; c0[1] += x['size']
                acost[(x['account'], x['outcome'])] = acost.get((x['account'], x['outcome']), 0.0) + x['usdc_size']
        # each account's own main side (largest held cost); a market is two-sided when accounts' main sides differ
        acc_main = {}
        for (ac, o), v in acost.items():
            if v > acost.get((ac, acc_main.get(ac, '')), -1): acc_main[ac] = o
        acc_sides = sorted(set(acc_main.values()))
        stake = sum(x['usdc_size'] for x in buys)
        first = min(x['timestamp'] for x in buys)
        before = sum(x['usdc_size'] for x in buys if filed and x['timestamp'] < filed.timestamp())
        sells = sum(x['usdc_size'] for x in fl if x['side'] == 'SELL')
        accts = sorted({x['account'] for x in buys})
        red = sum(r['usdc_size'] for r in rows if r['condition_id'] == c and r['type'] == 'REDEEM' and (scope == 'all22' or r['account'] not in EXPANDED))
        sides = sorted(cost)
        main = max(sides, key=lambda s: cost[s][0]) if sides else ''
        p = cost[main][0] / cost[main][1] if sides else None
        out.append({'scope': scope, 'condition_id': c, 'ticker': t, 'auditor': aud, 'title': title, 'slug': m['slug'], 'winner': winner,
                    'held_at_cutoff': bool(sides), 'cutoff': 'SEC_ITEM_2.02' if filed else 'MARKET_CLOSE', 'sides_held': '|'.join(sides), 'main_side': main,
                    'account_sides': '|'.join(acc_sides), 'every_account_side_won': bool(sides) and winner is not None and acc_sides == [winner], 'main_side_won': bool(sides) and winner == main,
                    'p_main_side_cost_weighted': round(p, 6) if p else '', 'held_cost_by_side': json.dumps({o: round(v[0], 2) for o, v in cost.items()}), 'stake_usdc': round(stake, 2), 'sells_usdc': round(sells, 2), 'redeem_usdc': round(red, 2),
                    'cash_result_usdc': round(sells + red - stake, 2), 'n_accounts': len(accts), 'accounts': '|'.join(accts),
                    'first_buy_utc': utc(first).isoformat(), 'sec_item202_acceptance_utc': filed.isoformat() if filed else '',
                    'hours_first_buy_before_filing': round((filed.timestamp() - first) / 3600, 2) if filed else '',
                    'stake_before_filing_usdc': round(before, 2) if filed else '', 'stake_after_filing_usdc': round(stake - before, 2) if filed else ''})
keys = list(out[0])
with open(OUT / 'kpmg_earnings_markets.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(sorted(out, key=lambda r: (r['scope'], r['auditor'], r['ticker'], r['slug'])))
def tail(ps, k):
    """Exact P(W >= k) for independent Bernoulli(p_i) (Poisson-binomial)."""
    d = [1.0]
    for p in ps: d = [a * (1 - p) + b * p for a, b in itertools.zip_longest(d + [0.0], [0.0] + d, fillvalue=0.0)]
    return sum(d[k:])
stats = {}
for scope in ('core19', 'all22'):
    for grp in sorted({r['auditor'] for r in out}):
        ms = [r for r in out if r['scope'] == scope and r['auditor'] == grp and r['winner'] is not None and r['held_at_cutoff']]
        if not ms: continue
        ps = [r['p_main_side_cost_weighted'] for r in ms]
        for rule in ('every_account_side_won', 'main_side_won'):
            k = sum(r[rule] for r in ms)
            stats[f'{scope}|{grp}|{rule}'] = {'markets': len(ms), 'wins': k, 'expected': round(sum(ps), 2), 'p_tail': tail(ps, k),
                                              'stake': round(sum(r['stake_usdc'] for r in ms), 2), 'cash_result': round(sum(r['cash_result_usdc'] for r in ms), 2)}
json.dump(stats, open(OUT / 'kpmg_market_stats.json', 'w'), indent=1)
for k, v in stats.items(): print(k, v)
# Sensitivity: markets where Youaregu (the pre-network account) is the only holder are dropped; Sidak over the four Big Four groups.
for rule in ('every_account_side_won', 'main_side_won'):
    ms = [r for r in out if r['scope'] == 'core19' and r['auditor'] == 'KPMG' and r['winner'] is not None and r['held_at_cutoff'] and r['accounts'] != 'Youaregu']
    ps = [r['p_main_side_cost_weighted'] for r in ms]; k = sum(r[rule] for r in ms)
    stats[f'core19|KPMG_without_Youaregu_only_markets|{rule}'] = {'markets': len(ms), 'wins': k, 'expected': round(sum(ps), 2), 'p_tail': tail(ps, k)}
    p = stats[f'core19|KPMG|{rule}']['p_tail']; stats[f'core19|KPMG|{rule}|sidak_4_auditors'] = 1 - (1 - p) ** 4
json.dump(stats, open(OUT / 'kpmg_market_stats.json', 'w'), indent=1)
for k in [k for k in stats if 'Youaregu' in k or 'sidak' in k]: print(k, stats[k])
assert abs(tail([0.5, 0.5], 2) - 0.25) < 1e-12 and abs(tail([0.5] * 3, 0) - 1) < 1e-12  # self-check of the exact tail
