"""Offline. Two passes in stream over state/out_full. Pass 1: who sends straight into a source (deposit-like addresses). Pass 2: one line per outgoing row with its class, and one record per (chain, recipient).
Writes data/outgoing_transactions.csv.gz, state/recipients.csv, state/source_periods.csv, state/norm_stats.json. RSS capped."""
import csv, glob, gzip, json, resource, sys, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import sources as S
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'state/out_full'
ZERO = '0x' + '0' * 40
RSS_CAP = 1200 * 1024 * 1024
win = json.loads((ROOT / 'state/window.json').read_text())
T0, T1 = win['t_start'], win['t_end']
tok = {(int(r['chain']), r['contract']): r for r in csv.DictReader(open(ROOT / 'state/tokens.csv'))}
prices = json.loads((ROOT / 'state/prices_daily.json').read_text())
cn = {r['address'] for r in csv.DictReader(open(ROOT / 'data/attribution_sources.csv'))} | {a for _, a in S.ETIQUETEE | S.CANDIDAT}
HUBS = S.ETIQUETEE | S.CANDIDAT
TX, TK, IN = 'txlist', 'tokentx', 'txlistinternal'


def files():
    for p in sorted(glob.glob(str(OUT / '*.csv.gz'))):
        name = Path(p).name[:-7]
        chain, addr, action = name.split('_', 2)
        yield int(chain), addr, action, p


def rows(p):
    with gzip.open(p, 'rt', newline='') as f:
        yield from csv.reader(f)


def price(chain, contract, ts):
    key = f'native:{42161 if chain == 1 else chain}' if contract is None else f'{chain}:{contract}'  # Ethereum and Arbitrum share the ETH series
    day = time.strftime('%Y-%m-%d', time.gmtime(ts))
    return (prices.get(key) or {}).get(day)


# Pass 1: senders into a source, recognised value only, inside the window
into = defaultdict(lambda: [0, 0, 0])  # (chain, addr) -> [token rows, native rows, first ts]
for chain, addr, action, p in files():
    if (chain, addr) not in HUBS:
        continue
    for r in rows(p):
        t = int(r[1])
        if not (T0 <= t <= T1) or r[4].lower() != addr or r[3].lower() == addr or r[5] == '0':
            continue
        a = r[3].lower()
        if action == TK:
            if tok.get((chain, r[6].lower()), {}).get('recognised') != 'True':
                continue
            into[(chain, a)][0] += 1
        elif action == TX:
            if r[6] != '0':
                continue
            into[(chain, a)][1] += 1
        else:
            continue
        v = into[(chain, a)]
        v[2] = min(v[2], t) if v[2] else t
print('senders into sources', len(into), 'rss', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 2**20, flush=True)

# Pass 2
stats = Counter()
per = defaultdict(lambda: dict(out=0, rcpt=Counter()))
rec = {}
HEAD = 'chain,source,source_tier,period,recipient,tx_hash,block,timestamp,utc,kind,token,contract,raw,decimals,amount,usd,class,function_probable,attribution_confidence'.split(',')
CONF = {(1, S.HOT3): 'elevee', (1, S.HOT4): 'elevee', (1, S.DEP): 'moyenne', (1, S.CN13): 'elevee', (42161, S.ARB): 'elevee', (1, S.HUB): 'comportementale', (1, S.GAS): 'comportementale', (137, S.POLY): 'faible'}
with gzip.open(ROOT / 'data/outgoing_transactions.csv.gz', 'wt', newline='', compresslevel=6) as fo:
    w = csv.writer(fo)
    w.writerow(HEAD)
    for chain, addr, action, p in files():
        tr = S.tier(chain, addr)
        nat = S.NATIVE[chain]
        for r in rows(p):
            t = int(r[1])
            if r[3].lower() != addr:
                continue
            stats[f'{tr}:out_rows'] += 1
            if not (T0 <= t <= T1):
                stats['hors_fenetre'] += 1
                continue
            to = r[4].lower()
            if action == TK:
                contract, sym, dec = r[6].lower(), r[7], int(r[8] or 0)
                kind = 'erc20'
                good = tok.get((chain, contract), {}).get('recognised') == 'True'
                bad = None if good else 'jeton_non_reconnu'
            else:
                contract, sym, dec = None, nat, 18
                kind = 'natif' if action == TX else 'interne'
                bad = None if r[6] == '0' else 'echec'
            raw = int(r[5] or 0)
            if bad is None and raw == 0:
                bad = 'valeur_nulle'
            if bad is None and (to == ZERO or not to):
                bad = 'burn_ou_creation'
            if bad:
                stats[f'{tr}:{bad}'] += 1
                continue  # poison, failed and zero-value rows are counted, not listed
            if to in cn:
                cls = 'interne_etiquette'
            elif (chain, to) in into and to not in cn:
                cls = 'depot_service_probable'
            else:
                cls = 'externe'
            period = 'avant_rotation' if t < S.ROTATION else 'apres_rotation'
            amount = raw / 10 ** dec
            pr = price(chain, contract, t)
            usd = round(amount * pr, 2) if pr is not None else ''
            w.writerow([S.CHAIN[chain], addr, tr, period, to, r[2], r[0], t, time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t)), kind, sym, contract or '', raw, dec, f'{amount:.8f}', usd, cls, '', CONF.get((chain, addr), 'structurelle')])
            stats[f'{tr}:{cls}'] += 1
            stats[f'{tr}:{kind}'] += 1
            k = (chain, addr, period, kind)
            per[k]['out'] += 1
            per[k]['rcpt'][to] += 1
            if tr == 'AUTRE' or cls == 'interne_etiquette':
                continue
            v = rec.get((chain, to, tr))
            if v is None:
                v = rec[(chain, to, tr)] = dict(first=t, src=addr, tx=r[2], n=0, last=t, usd=0.0, no_price=0, cls=set(), assets=Counter(), kinds=set())
            if t < v['first']:
                v.update(first=t, src=addr, tx=r[2])
            v['last'] = max(v['last'], t)
            v['n'] += 1
            v['cls'].add(cls)
            v['kinds'].add(kind)
            v['assets'][f'{sym}|{contract or "natif"}|{dec}'] += raw
            if usd == '':
                v['no_price'] += 1
            else:
                v['usd'] += usd
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > RSS_CAP:
            raise SystemExit('rss cap')
        print(chain, addr[:10], action, 'recipients', len(rec), flush=True)
with (ROOT / 'state/recipients.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow('chain,recipient,tier,first_ts,first_source,first_tx,last_ts,n_transfers,usd,rows_no_usd,classes,kinds,assets,into_token_rows,into_native_rows'.split(','))
    for (c, a, tr), v in rec.items():
        i = into.get((c, a), (0, 0, 0))
        w.writerow([c, a, tr, v['first'], v['src'], v['tx'], v['last'], v['n'], round(v['usd'], 2), v['no_price'], '|'.join(sorted(v['cls'])), '|'.join(sorted(v['kinds'])), json.dumps({k: str(x) for k, x in v['assets'].items()}), i[0], i[1]])
with (ROOT / 'state/source_periods.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow('chain,source,tier,period,kind,n_out,uniq_rcpt,rcpt_once,share_once,top_rcpt,top_share,function_rule'.split(','))
    for (c, a, pd, kind), v in sorted(per.items()):
        rc = v['rcpt']
        once = sum(x == 1 for x in rc.values())
        (top, tn) = rc.most_common(1)[0]
        fn = 'PAYOUT_HOT' if v['out'] >= 100 and len(rc) >= 50 and once / len(rc) >= .5 else 'CONSOLIDATION' if v['out'] >= 20 and (len(rc) <= 10 or tn / v['out'] >= .5) else 'INCONNUE'
        w.writerow([c, a, S.tier(c, a), pd, kind, v['out'], len(rc), once, round(once / len(rc), 3), top, round(tn / v['out'], 3), fn])
(ROOT / 'state/norm_stats.json').write_text(json.dumps(dict(stats=stats, recipients=len(rec), senders_into=len(into), rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 2**20), indent=0))
print(json.dumps(stats, indent=0))
