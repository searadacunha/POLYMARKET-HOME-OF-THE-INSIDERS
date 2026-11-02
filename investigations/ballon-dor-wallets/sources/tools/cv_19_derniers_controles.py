"""Derniers contrôles : créneau du 24 oct. (sans réseau), sceau et filtre E4 (sans réseau), comptage des lots partagés, nom de SwftSwap et soldes aux blocs (3 à 8 lectures publiques, ni BSC ni saut 0x7e67)."""
import glob, gzip, hashlib, json, os, random, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
U = lambda t: time.strftime('%m-%d %H:%M:%S', time.gmtime(t))
res = {}


def rpc(node, method, params):
    time.sleep(.4)
    req = urllib.request.Request(node, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=40))
        return d.get('result') if 'error' not in d else None
    except Exception:
        return None


# 1. Créneau du 24 oct., 14:00 à 17:00 UTC
tr = json.load(open(OUT / 'trades_kane.json'))['24_oct']
yes = [r for r in tr if str(r['o']).lower() == 'yes']
B_W, K_W, Z_W = '0x873848cd27784900e193611845fc3fd2c4716d03', '0x84212ee459d1edaf35983bbec342b0806282d8ec', '0x92a8eec13a691af81a1a196b7594c1eccfa0eebc'
buy = [r for r in yes if r['s'] == 'BUY']
tot = sum(r['z'] * r['p'] for r in buy)
by = {}
for r in buy:
    by.setdefault(r['w'], []).append(r)
res['creneau'] = dict(lignes=len(tr), lignes_yes=len(yes), achats_yes_usd=round(tot, 2), acheteurs=len(by), part_brace_pct=round(100 * sum(r['z'] * r['p'] for r in by.get(B_W, [])) / tot, 1), part_kraben_pct=round(100 * sum(r['z'] * r['p'] for r in by.get(K_W, [])) / tot, 1), part_zoomman_pct=round(100 * sum(r['z'] * r['p'] for r in by.get(Z_W, [])) / tot, 1), brace_usd=round(sum(r['z'] * r['p'] for r in by.get(B_W, [])), 2), kraben_usd=round(sum(r['z'] * r['p'] for r in by.get(K_W, [])), 2), zoomman_usd=round(sum(r['z'] * r['p'] for r in by.get(Z_W, [])), 2))
res['creneau']['top_acheteurs'] = sorted(((w[:10], len(v), round(sum(r['z'] * r['p'] for r in v))) for w, v in by.items()), key=lambda x: -x[2])[:8]
res['creneau']['prix_debut_fin'] = (round(sorted(yes, key=lambda r: r['t'])[0]['p'], 3), round(sorted(yes, key=lambda r: r['t'])[-1]['p'], 3))
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
A, Z = 1792850400, 1792861200
t_of = lambda s: sorted(r['timestamp'] for r in act[s] if r['type'] == 'TRADE' and r.get('side') == 'BUY' and 'Harry Kane win' in (r.get('title') or '') and float(r.get('usdc_size') or 0) >= 100 and A <= r['timestamp'] < Z)
tb, tk = t_of('brace227'), t_of('kraben006')
near = lambda xs, ys: sum(1 for x in xs if any(abs(x - y) <= 300 for y in ys))
obs = near(tb, tk)
# Nul local : décalage circulaire à l'intérieur du seul créneau de 3 h, garde le rythme de chaque compte, ne garde pas une vague de marché minute par minute
rng = random.Random(20261102)
L = Z - A
draws = [near(tb, [A + (y - A + rng.uniform(600, L - 600)) % L for y in tk]) for _ in range(20000)]
res['creneau']['brace_proches_de_kraben'] = obs
res['creneau']['n_brace'], res['creneau']['n_kraben'] = len(tb), len(tk)
res['creneau']['p_decalage_dans_le_creneau'] = round((sum(d >= obs for d in draws) + 1) / 20001, 4)
res['creneau']['moyenne_nulle'] = round(sum(draws) / len(draws), 2)
res['creneau']['heures'] = (U(tb[0]), U(tb[-1]), U(tk[0]), U(tk[-1]))
sells = {s: [(U(r['timestamp']), round(r['usdc_size']), r['title'][:24], r['outcome']) for r in act[s] if r['type'] == 'TRADE' and r.get('side') == 'SELL' and A - 7200 <= r['timestamp'] < Z + 7200 and r['usdc_size'] >= 100] for s in ('brace227', 'kraben006', 'zoomman17')}
res['creneau']['ventes_autour'] = {k: v[:10] for k, v in sells.items()}
# 2. Sceau de la partie A
seal = json.load(open(ROOT / 'collective/derived/A_seal.json'))
res['sceau'] = dict(sealed_at=seal['sealed_at'], fichiers=len(seal['sha256']), differents=[f for f, h in seal['sha256'].items() if hashlib.sha256((ROOT / 'collective' / f).read_bytes()).hexdigest() != h])
# 3. Filtre de E4 dans le code gelé, absent du plan
src = (ROOT / 'collective/code/ana_overlap_core_v2.py').read_text()
res['filtre_e4_code'] = [l.strip() for l in src.splitlines() if '>= 2' in l or '>=2' in l or '100' in l][:6]
res['plan_e4_mentionne_2_tokens'] = '2 tokens' in (ROOT / 'collective/analysis_plan.md').read_text()
# 4. Lots partagés : combien de comptes dans chaque transaction de redemption
POLY = 'https://polygon-bor-rpc.publicnode.com'
ev = json.load(open(OUT / 'calendrier_kane.json'))
topic = ev['topic']
res['lots'] = {}
for tx in ('0x0b9768d113b099417a8504cdfb54f4ad2c4837923bde06677b5c28e4f3611f70', '0x125aee8279c00137877e4139ea0b9d952467140ca4e232a437b04d1b720bc4fa', '0xa224d967e60fbcc14e9ee5ffd5db1e0e3b7c8882d658349b77a579df2d9d1af9'):
    rc = rpc(POLY, 'eth_getTransactionReceipt', [tx])
    res['lots'][tx] = len({l['topics'][1] for l in rc['logs'] if l['topics'][0] == topic}) if rc else None
res['lot_kane'] = dict(comptes=len(ev['events']), tx=len({e['tx'] for e in ev['events']}), somme=round(sum(e['amount'] for e in ev['events']), 2), premier=U(min(e['ts'] for e in ev['events'])), dernier=U(max(e['ts'] for e in ev['events'])), resolution=ev['resolution'][0]['utc'], sup_5000=sum(e['amount'] >= 5000 for e in ev['events']))
# 5. Nom du contrat et soldes aux blocs
try:
    i = json.load(urllib.request.urlopen(urllib.request.Request('https://eth.blockscout.com/api/v2/addresses/0xc1d13492285eb664951e201bf7c80c7c6318a1b5', headers={'User-Agent': 'read-only'}), timeout=30))
    res['swftswap'] = dict(name=i.get('name'), verified=i.get('is_verified'), contract=i.get('is_contract'))
except Exception as e:
    res['swftswap'] = str(e)[:80]
want = {('0xc852b0938f5ad79b640d105ed11c14499454af26', 26119411): 2072705767437553, ('0xc852b0938f5ad79b640d105ed11c14499454af26', 26119420): 494489646000}
res['archive'] = {}
for node in ('https://eth.drpc.org', 'https://1rpc.io/eth'):
    for (a, b), v in want.items():
        got = rpc(node, 'eth_getBalance', [a, hex(b)])
        res['archive'][f'{node}|{b}'] = (int(got, 16), v, int(got, 16) == v) if got else None
(OUT / 'derniers_controles.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res, indent=0, ensure_ascii=False))
