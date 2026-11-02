"""Registry step 2: measured behaviour of every address some source calls ChangeNOW, plus unlabeled hubs seen moving funds with them, on the chains readable for free. Last 1000 rows per action, recognised tokens only. Function rules are in PLAN.md. Writes state/registry_behaviour.csv and state/token_prices_now.json."""
import csv, gzip, json, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
ROOT = net.ROOT
P = Path.home() / 'Projects/PolySentinel-ChangeNOW-proof'
LLAMA = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum', 10: 'optimism'}
CHAINS = (1, 137, 42161)
T_90 = time.time() - 90 * 86400
HUBS = '0x64cdaa89629fe003eaa31b480d8b63372d109a53 0x300773969b499b9768267e0c5a049f7751de79e7 0x45300136662dd4e58fc0df61e6290dffd992b785 0x41e457717052a9f80fb2a5a06caccda18469fb17 0x2458b3ad07e88b78d0204525d9cbf445c22843e7 0x19f00b3a7b6f55c9da966fe3723251784a797fa7 0xd91efec7e42f80156d1d9f660a69847188950747 0x58edf78281334335effa23101bbe3371b6a36a51 0x83c41363cbee0081dab75cb841fa24f3db46627e'.split()

labels = {}
for r in csv.DictReader(open(P / 'state/universe_raw.csv')):
    if r['address'].startswith('0x'):
        labels.setdefault(r['address'], set()).add(r['name'])
tagfile = ROOT / 'state/bs_tags.jsonl'
if tagfile.exists():
    for line in open(tagfile):
        v = json.loads(line)
        n = v['name'] or ''
        # one-address client deposit tags and hacker tags are internal or foreign by name: kept for matching in reg3, not worth a behaviour read
        if 'change' in n.lower() and 'now' in n.lower() and not n.startswith(('ChangeNOW_Deposit', 'Upbit Hacker')) and v['slug'] not in ('changenow', 'changenow-dep'):
            for a in v['addresses']:
                labels.setdefault(a, set()).add(n)
for a in HUBS:
    labels.setdefault(a, set()).add('(sans étiquette, hub observé)')


def recognised(chain, contracts):
    """Contract -> price, only when DeFiLlama prices it with confidence >= .9. Fake tickers have no price."""
    out = {}
    cs = sorted(contracts)
    for i in range(0, len(cs), 80):
        d = net.get('https://coins.llama.fi/prices/current/' + ','.join(f'{LLAMA[chain]}:{c}' for c in cs[i:i + 80]), pause=.5)
        for k, v in (d.get('coins') or {}).items():
            if (v.get('confidence') or 0) >= .9:
                out[k.split(':')[1].lower()] = v['price']
    return out


rows = []
for a, names in sorted(labels.items()):
    for chain in CHAINS:
        tx = es.rows('txlist', a, chain, sort='desc')
        tok = es.rows('tokentx', a, chain, sort='desc')
        if not tx and not tok:
            continue
        ok = recognised(chain, {r['contractAddress'].lower() for r in tok})
        good = [r for r in tok if r['contractAddress'].lower() in ok]
        for act, rs in (('natif', [r for r in tx if int(r['value']) > 0 and r.get('isError') == '0']), ('jetons', good)):
            ts = [int(r['timeStamp']) for r in rs]
            outs = [r for r in rs if r['from'].lower() == a]
            ins = [r for r in rs if (r['to'] or '').lower() == a]
            rc, sc = Counter((r['to'] or '').lower() for r in outs), Counter(r['from'].lower() for r in ins)
            span = (max(ts) - min(ts)) / 86400 if len(ts) > 1 else 0
            rows.append(dict(address=a, chain=chain, labels='|'.join(sorted(names)), action=act, read_tx=len(tx), read_tok=len(tok), spoof_rows=len(tok) - len(good), rows=len(rs), span_days=round(span, 3), per_day=round(len(rs) / span, 1) if span else '', last=max(ts) if ts else '', first=min(ts) if ts else '', active_90d=bool(ts and max(ts) >= T_90), n_out=len(outs), n_in=len(ins), uniq_rcpt=len(rc), uniq_sndr=len(sc), rcpt_once=sum(v == 1 for v in rc.values()), sndr_once=sum(v == 1 for v in sc.values()), top_rcpt=round(max(rc.values()) / len(outs), 3) if outs else '', top_rcpt_addr=rc.most_common(1)[0][0] if rc else '', tokens=' '.join(f'{k}:{v}' for k, v in Counter(r.get('tokenSymbol', '') for r in rs).most_common(5)) if act == 'jetons' else ''))
        print(a[:10], chain, len(tx), len(tok), flush=True)
with (ROOT / 'state/registry_behaviour.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print('rows', len(rows), 'addresses', len({r['address'] for r in rows}))
