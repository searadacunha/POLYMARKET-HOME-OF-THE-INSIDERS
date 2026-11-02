"""Part A, E4 version 2, amendment 002. Three explicit seeds; writes A_E4_v2.json and leaves A_E4.json alone."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R
from ana_overlap_core_v2 import run
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = Path(ETUDE)
SEEDS = (20261101, 20261102, 20261103)
out_name = sys.argv[1] if len(sys.argv) > 1 else 'derived/A_E4_v2.json'
seeds = SEEDS if len(sys.argv) < 3 else tuple(int(x) for x in sys.argv[2].split(','))
rows = [r for r in R.family() if r[0] == 'M']
out = {}
for name, end in (('D2', R.D2), ('T_FIN', R.T_FIN)):
    for seed in seeds:
        key = f'{name}_{seed}'
        out[key] = run(rows, end, seed=seed)
        print(key, {k: out[key][k] for k in ('wallets', 'tokens', 'pairs_sharing', 'pairs_above_null_max', 'max_shared')}, flush=True)
(E / out_name).write_text(json.dumps(out, sort_keys=True))
if len(sys.argv) < 2:
    enregistrer(ETUDE, 'E4_v2_overlap', True, out['T_FIN_20261101']['wallets'], 'claude', n_effectif=1, n_tirages=200, n_comparaisons=sum(v['pairs_sharing'] for v in out.values()), sortie=out_name, params=dict(seeds=list(seeds)), note='Amendment 002, written after results were read.')
