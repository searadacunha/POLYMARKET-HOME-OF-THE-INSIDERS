"""Which contracts are real tokens, and their daily prices. Scans every collected token row, asks DeFiLlama. Unpriced or low-confidence contracts are excluded from economic volumes and counted apart. Writes state/tokens.csv, state/prices_daily.json."""
import csv, glob, gzip, json, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
ROOT = net.ROOT
LLAMA = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum'}
NATIVE = {1: 'coingecko:ethereum', 137: 'coingecko:polygon-ecosystem-token', 42161: 'coingecko:ethereum'}
win = json.loads((ROOT / 'state/window.json').read_text())
cnt, sym, dec = Counter(), {}, {}
for p in glob.glob(str(ROOT / 'state/out_full/*_tokentx.csv.gz')):
    chain = int(Path(p).name.split('_')[0])
    with gzip.open(p, 'rt', newline='') as f:
        for r in csv.reader(f):
            k = (chain, r[6].lower())
            cnt[k] += 1
            sym.setdefault(k, r[7])
            dec.setdefault(k, r[8])
print('contracts', len(cnt), 'rows', sum(cnt.values()), flush=True)
now = {}
keys = sorted(cnt)
for i in range(0, len(keys), 80):
    d = net.get('https://coins.llama.fi/prices/current/' + ','.join(f'{LLAMA[c]}:{a}' for c, a in keys[i:i + 80]), pause=.5)
    for k, v in (d.get('coins') or {}).items():
        ch, a = k.split(':')
        now[({v2: k2 for k2, v2 in LLAMA.items()}[ch], a.lower())] = v
ok = {k for k, v in now.items() if (v.get('confidence') or 0) >= .9}
with (ROOT / 'state/tokens.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['chain', 'contract', 'symbol', 'decimals', 'rows', 'recognised', 'llama_confidence', 'price_now'])
    for k, n in cnt.most_common():
        v = now.get(k, {})
        w.writerow([k[0], k[1], sym[k], dec[k], n, k in ok, v.get('confidence', ''), v.get('price', '')])
print('recognised', len(ok), 'rows in recognised', sum(cnt[k] for k in ok), flush=True)
# daily prices for tokens covering 99.5 % of recognised rows, and natives
total = sum(cnt[k] for k in ok)
run, chosen = 0, []
for k, n in sorted(((k, cnt[k]) for k in ok), key=lambda x: -x[1]):
    if run >= .995 * total:
        break
    chosen.append(k)
    run += n
prices = {}
start, span = win['t_start'] - 86400, 95
coins = {f'{LLAMA[c]}:{a}': f'{c}:{a}' for c, a in chosen} | {v: f'native:{k}' for k, v in NATIVE.items()}
for coin, key in coins.items():
    d = net.get(f'https://coins.llama.fi/chart/{coin}', dict(start=start, span=span, period='1d'), pause=.5)
    pts = next(iter((d.get('coins') or {}).values()), {}).get('prices') or []
    prices[key] = {time.strftime('%Y-%m-%d', time.gmtime(p['timestamp'])): p['price'] for p in pts}
    print(key, sym.get(tuple(key.split(':')) if False else None, ''), len(pts), flush=True)
(ROOT / 'state/prices_daily.json').write_text(json.dumps(prices))
print('priced', len(prices), 'of chosen', len(chosen))
