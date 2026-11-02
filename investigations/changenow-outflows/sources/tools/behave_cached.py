"""Offline: behaviour of every address some source calls ChangeNOW, from answers already cached by the proof session. No network. Prints one line per address/action."""
import csv, gzip, hashlib, json, sys, urllib.parse, datetime as D
from collections import Counter
from pathlib import Path
P = Path.home() / 'Projects/PolySentinel-ChangeNOW-proof'
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
INV = Path.home() / 'Projects/PolySentinel-investigation'
CACHES = [P / 'state/http_cache', FT / 'state/http_cache', INV / 'state/http_cache']
def load(url):
    k = hashlib.sha256(url.encode()).hexdigest()
    for c in CACHES:
        f = c / k[:2] / (k + '.json.gz')
        if f.exists():
            return json.load(gzip.open(f, 'rt'))
def url(action, a, chain=1, sort='desc'):
    return 'https://api.etherscan.io/v2/api?' + urllib.parse.urlencode(dict(chainid=chain, module='account', action=action, address=a, page=1, offset=1000, sort=sort, startblock=0, endblock=999999999))
names = {}
for r in csv.DictReader(open(P / 'state/universe_raw.csv')):
    if r['address'].startswith('0x'):
        names.setdefault(r['address'], set()).add(r['name'])
f = lambda t: D.datetime.fromtimestamp(t, D.UTC).strftime('%Y-%m-%d')
w = csv.writer(sys.stdout)
w.writerow('address name action read span_days rows_per_day first last n_out n_in uniq_rcpt uniq_sndr rcpt_once sndr_once top_rcpt_share tokens'.split())
for a, n in sorted(names.items()):
    for act in ('txlist', 'tokentx'):
        d = load(url(act, a))
        if d is None or d.get('status') != '1':
            continue
        rows = d['result']
        ts = [int(r['timeStamp']) for r in rows]
        outs = [r for r in rows if r['from'].lower() == a and (act == 'tokentx' or (int(r['value']) > 0 and r.get('isError') == '0'))]
        ins = [r for r in rows if (r['to'] or '').lower() == a and (act == 'tokentx' or (int(r['value']) > 0 and r.get('isError') == '0'))]
        rc, sc = Counter(r['to'].lower() for r in outs), Counter(r['from'].lower() for r in ins)
        span = (max(ts) - min(ts)) / 86400
        w.writerow([a, '|'.join(sorted(n))[:40], act, len(rows), round(span, 2), round(len(rows) / span) if span else '', f(min(ts)), f(max(ts)), len(outs), len(ins), len(rc), len(sc), sum(v == 1 for v in rc.values()), sum(v == 1 for v in sc.values()), round(max(rc.values()) / len(outs), 3) if outs else '', ' '.join(f'{k}:{v}' for k, v in Counter(r.get('tokenSymbol', '') for r in rows).most_common(4)) if act == 'tokentx' else ''])
