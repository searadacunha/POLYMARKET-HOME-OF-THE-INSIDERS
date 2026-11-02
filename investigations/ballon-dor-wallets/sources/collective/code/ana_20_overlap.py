"""Part A, E4 runner. Core in ana_overlap_core."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R
from ana_overlap_core import run
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = Path(ETUDE)
rows = [r for r in R.family() if r[0] == 'M']
out = {}
for name, end in (('D2', R.D2), ('T_FIN', R.T_FIN)):
    out[name] = run(rows, end)
    (E / 'derived/A_E4.json').write_text(json.dumps(out))
    enregistrer(ETUDE, f'E4_overlap_{name}', True, out[name]['wallets'], 'claude', n_effectif=1, stat=out[name]['pairs_above_null_max'], n_tirages=out[name]['draws'], n_comparaisons=out[name]['pairs_sharing'], sortie='derived/A_E4.json')
    print(name, json.dumps({k: v for k, v in out[name].items() if k not in ('top', 'null_max_by_shared')}))
