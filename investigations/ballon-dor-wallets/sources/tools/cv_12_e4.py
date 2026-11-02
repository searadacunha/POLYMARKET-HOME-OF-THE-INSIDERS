"""Contre-vérification : E4 v2 relancé sous un autre hachage, trois graines, sans rien écrire dans collective/. Couverture des paires nommées."""
import glob, hashlib, itertools, json, os, sys, time
sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + '/collective/code')
import rows as R
from ana_overlap_core_v2 import run, matrix
OUT = ROOT + '/evidence/contre_verification_20261102/e4_reproduction.json'
named = {json.load(open(f))['address'].lower(): os.path.basename(f)[:-5] for f in glob.glob(ROOT + '/cases/*.json')}
rows = [r for r in R.family() if r[0] == 'M']
stored = json.load(open(ROOT + '/collective/derived/A_E4_v2.json'))
res = dict(hash_seed=os.environ.get('PYTHONHASHSEED'), rows=len(rows), runs={})
for name, end in (('D2', R.D2), ('T_FIN', R.T_FIN)):
    m = matrix(rows, end)
    inside = sorted(named[w] for w in m if w in named)
    res[name] = dict(univers=len(m), nommes_dans_univers=inside, nommes_hors=sorted(set(named.values()) - set(inside)), paires_nommees_testees=len(inside) * (len(inside) - 1) // 2, paires_non_testees=55 - len(inside) * (len(inside) - 1) // 2)
    for seed in (20261101, 20261102, 20261103):
        t = time.time()
        out = run(rows, end, seed=seed)
        same = json.dumps(out, sort_keys=True) == json.dumps(stored[f'{name}_{seed}'], sort_keys=True)
        res['runs'][f'{name}_{seed}'] = dict(identique=same, paires=out['pairs_above_null_max'], s=round(time.time() - t, 1))
        print(name, seed, 'identique', same, 'paires', out['pairs_above_null_max'], round(time.time() - t, 1), flush=True)
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('D2', 'T_FIN')}, indent=0))
