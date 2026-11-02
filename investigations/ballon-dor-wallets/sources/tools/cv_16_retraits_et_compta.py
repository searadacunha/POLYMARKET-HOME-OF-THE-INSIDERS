"""Contre-vérification sans réseau. Burn pUSD des 25 retraits relu depuis le cache de receipts, réconciliation exacte des périmètres, allers-retours."""
import glob, gzip, hashlib, json, os, time
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102/reconciliation_montants.json'
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO = '0x' + '0' * 64
U = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))


def receipt(tx):
    key = hashlib.sha256(json.dumps([137, 'eth_getTransactionReceipt', [tx]]).encode()).hexdigest()
    for c in (ROOT / 'state/http_cache', ROOT / 'collective/state/http_cache'):
        p = c / key[:2] / (key + '.json.gz')
        if p.exists():
            with gzip.open(p, 'rt') as f:
                return json.load(f)
    return None


cases = {Path(f).stem: json.load(open(f)) for f in sorted(glob.glob(str(ROOT / 'cases/*.json')))}
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
res = dict(par_dossier={})
miss, bad, burn_sum, no_exit = [], [], 0., []
mint_miss, mint_bad, mint_sum = [], [], 0.
for s, c in cases.items():
    w = '0x' + '0' * 24 + c['address'].lower()[2:]
    for x in c['withdrawals']:
        rc = receipt(x['tx'])
        if not rc:
            miss.append(x['tx'])
            continue
        # le burn part d'un contrat intermédiaire, pas du wallet : on exige une sortie du wallet et une destruction du même montant
        v = [int(l['data'], 16) / 1e6 for l in rc['logs'] if l['address'].lower() == PUSD and l['topics'][0] == TRANSFER and l['topics'][2] == ZERO]
        sent = [int(l['data'], 16) / 1e6 for l in rc['logs'] if l['address'].lower() == PUSD and l['topics'][0] == TRANSFER and l['topics'][1] == w and l['topics'][2] != ZERO]
        if not any(abs(a - x['usd']) < 1e-6 for a in sent):
            no_exit.append((s, x['tx'], sent, x['usd']))
        if len(v) != 1 or abs(v[0] - x['usd']) > 1e-6:
            bad.append((s, x['tx'], v, x['usd']))
        burn_sum += sum(v)
    for x in c['deposits']:
        rc = receipt(x['tx'])
        if not rc:
            mint_miss.append(x['tx'])
            continue
        v = [int(l['data'], 16) / 1e6 for l in rc['logs'] if l['address'].lower() == PUSD and l['topics'][0] == TRANSFER and l['topics'][1] == ZERO and l['topics'][2] == w]
        if len(v) != 1 or abs(v[0] - x['usd']) > 1e-6:
            mint_bad.append((s, x['tx'], v, x['usd']))
        mint_sum += sum(v)
res['burn'] = dict(lus_du_cache=25 - len(miss), absents_du_cache=len(miss), ecarts=bad, sans_sortie_du_wallet=no_exit, somme=round(burn_sum, 6))
res['mint'] = dict(lus_du_cache=46 - len(mint_miss), absents_du_cache=len(mint_miss), ecarts=mint_bad, somme=round(mint_sum, 6))
closed, open_, tot = {}, {}, defaultdict(float)
for s, c in cases.items():
    a = c['account']
    d, w = a['deposits'], a['withdrawals']
    row = dict(depots=round(d, 6), retraits=round(w, 6), net=round(w - d, 6), n_depots=len(c['deposits']), n_retraits=len(c['withdrawals']), solde=a['account_closed'], residu=a['residual'], par_type={k: round(v, 6) for k, v in a['by_type'].items()} if isinstance(a['by_type'], dict) else a['by_type'])
    res['par_dossier'][s] = row
    (closed if a['account_closed'] else open_)[s] = row
    if isinstance(a['by_type'], dict):
        for k, v in a['by_type'].items():
            tot[k] += v
sumk = lambda g, k: round(sum(v[k] for v in g.values()), 6)
res['totaux'] = dict(retraits_bruts_11=sumk(res['par_dossier'], 'retraits'), depots_bruts_11=sumk(res['par_dossier'], 'depots'), net_11=sumk(res['par_dossier'], 'net'), net_7_soldes=sumk(closed, 'net'), net_4_non_soldes=sumk(open_, 'net'), retraits_7=sumk(closed, 'retraits'), depots_7=sumk(closed, 'depots'), retraits_4=sumk(open_, 'retraits'), depots_4=sumk(open_, 'depots'), sept=sorted(closed), quatre=sorted(open_), par_type={k: round(v, 6) for k, v in tot.items()})
assert abs(res['totaux']['net_7_soldes'] + res['totaux']['net_4_non_soldes'] - res['totaux']['net_11']) < 1e-4
# Allers-retours : retrait suivi d'un dépôt de même montant, à 1 % près, en moins de 24 h, sur le même dossier
rt = []
for s, c in cases.items():
    for w in c['withdrawals']:
        for d in c['deposits']:
            if 0 < d['at'] - w['at'] < 86400 and abs(d['usd'] - w['usd']) / w['usd'] < .01:
                rt.append(dict(dossier=s, retrait=round(w['usd'], 2), retrait_utc=w['utc'], depot=round(d['usd'], 2), depot_utc=d['utc'], ecart_s=d['at'] - w['at']))
res['allers_retours'] = rt
res['allers_retours_usd'] = round(sum(x['retrait'] for x in rt), 2)
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in res.items() if k != 'par_dossier'}, indent=0, ensure_ascii=False))
for s, r in res['par_dossier'].items():
    print(s, r['n_depots'], r['n_retraits'], r['depots'], r['retraits'], r['net'], r['solde'], r['residu'])
