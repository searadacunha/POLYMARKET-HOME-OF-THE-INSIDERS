"""Positive controls, through the same functions as the real run. The null must stay silent, the strong must alert, and a cohort injected into a real control unit must be found."""
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R
import signals as K
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START, END = 1791000000, 1791000000 + 20 * 86400


def table(seed, cohort=0, usd=0, spread_h=40):
    rng = random.Random(seed)
    out, ages = [], {}
    # Background: many old wallets, plus many fresh wallets who stay small, and a few large old ones.
    for i in range(300):
        w = f'old{i}'
        ages[w] = START - 200 * 86400
        for _ in range(rng.randint(1, 6)):
            out.append(('T', 'e', 'tok', w, 'BUY', rng.uniform(5, 700), 1, .5, rng.randint(START, END), f'tx{w}{rng.random()}'))
    for i in range(60):
        w = f'freshsmall{i}'
        ages[w] = rng.randint(START, END - 86400)
        out.append(('T', 'e', 'tok', w, 'BUY', rng.uniform(5, 400), 1, .5, ages[w] + 3600, f'tx{w}'))
    at = START + 10 * 86400
    for i in range(cohort):
        w = f'coh{i}'
        ages[w] = at - 2 * 86400
        out.append(('T', 'e', 'tok', w, 'BUY', usd, 1, .5, at + int(i * spread_h * 3600 / max(cohort - 1, 1)), f'tx{w}'))
    return out, ages


results = []
for seed in (11, 29, 47):
    for name, cohort, usd, expect in (('nul', 0, 0, False), ('moyen', 3, 4000, True), ('moyen_sous_seuil', 2, 6000, False), ('fort', 8, 12000, True)):
        rows, ages = table(seed, cohort, usd)
        first, _ = K.alerts(K.by_token(rows), ages, END, START)
        results.append(dict(seed=seed, table=name, alert=bool(first), expected=expect, n=first.get('tok', {}).get('n')))
        assert bool(first) == expect, results[-1]
# Fills of one order count once, and a small-then-large sequence is seen.
assert K.decisions([(1, 'a', 10), (1, 'a', 20), (50, 'b', 5), (500, 'c', 7)]) == (3, [(1, 35), (500, 7)])
assert K.small_then_large([(1, 100), (2, 100), (3, 900), (4, 1500)])['index'] == 3
assert K.small_then_large([(1, 100), (2, 100)]) is None
b = K.bursts([(0, 'a', 300), (10, 'b', 300), (20, 'c', 300), (4000, 'd', 300)], 5)
assert len(b) == 1 and b[0]['wallets'] == 3
assert not K.bursts([(0, 'a', 9000), (10, 'b', 300), (20, 'c', 300)], 5)  # one wallet above 80 % is not a collective burst
# An unknown age never counts as fresh, and is reported.
assert K.fresh_cohort([(1, 'a', 2000), (2, 'b', 2000)], 3, {'a': 0})[0:1] == (1,) and K.fresh_cohort([(1, 'a', 2000), (2, 'b', 2000)], 3, {'a': 0})[3] == 1
# Injection into a real control unit: rows after the cohort cannot change the first alert, and only the injected cohort makes it fire.
real = [r for r in R.controls() if r[1] == 'south-carolina-governor-winner-2026']
token = real[0][2]
ages = {r[3]: r[8] - 400 * 86400 for r in real}
at = 1792000000
injected = real + [('X', 'inj', token, f'inj{i}', 'BUY', 4000.0, 1, .5, at + i * 3600, f'txinj{i}') for i in range(3)]
for i in range(3):
    ages[f'inj{i}'] = at - 86400
base, _ = K.alerts(K.by_token(real), ages, R.T_FIN, R.T0)
found, _ = K.alerts(K.by_token(injected), ages, R.T_FIN, R.T0)
assert not base and found[token]['n'] == 3 and found[token]['t'] >= at
results.append(dict(table='injection_reelle', unit='south-carolina-governor-winner-2026', rows=len(real), silent_before=not base, found_at=found[token]['t']))
out = Path(ETUDE) / 'controles/CONTROLES.json'
out.write_text(json.dumps(results, indent=1))
(Path(ETUDE) / 'controles/CONTROLES.md').write_text('# Contrôles positifs\n\nExécutés par `code/ctl_synth.py` sur tables synthétiques (3 graines) et une injection dans une vraie unité X.\n\n```json\n' + json.dumps(results, indent=1) + '\n```\n\nLe nul reste muet, le moyen à 3 wallets alerte, le moyen sous le seuil de N reste muet, le fort alerte. Table de puissance : sur ces tables, A0 détecte une cohorte d\'au moins 3 wallets à 4 000 $ chacun en moins de 72 h, et ne détecte pas 2 wallets. Puissance sur données réelles inconnue : aucun cas vérifié n\'existe.\n')
enregistrer(ETUDE, 'ctl_synth', True, len(results), 'claude', donnees='synthetiques', n_comparaisons=len(results), sortie='controles/CONTROLES.json')
print(json.dumps(results))
# E4: a planted pair sharing rare tokens beats the Curveball null; a matrix with no planted pair stays near it.
import ana_overlap_core as O
rng = random.Random(7)
m = {f'w{i}': set(rng.sample([f't{k}' for k in range(30)], 3)) for i in range(120)}
m['p1'] = {'rare1', 'rare2', 'rare3', 'rare4'}
m['p2'] = {'rare1', 'rare2', 'rare3', 'rare4'}
assert O.planted_beats_null(m, 'p1', 'p2')
print('E4 planted pair found')
