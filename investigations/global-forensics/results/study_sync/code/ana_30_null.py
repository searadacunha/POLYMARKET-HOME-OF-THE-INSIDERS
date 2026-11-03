"""H2 from the frozen table, then the verdict of the plan, written once."""
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana_20_primary as primary
import lib_bursts as lib
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = Path(ETUDE) / 'tables'


def main():
    _, entrants = primary.read()
    entrants = [r for r in entrants if not r['partial']]
    h1 = json.loads((TABLES / 'h1.json').read_text())
    count, verdicts = {}, {}
    for window in lib.WINDOWS:
        key = str(window)
        count[key] = lib.h2_test(entrants, window)
        verdicts[key] = lib.verdict(h1[key]['primary'], h1[key]['valid'], h1[key]['test'], h1[key]['placebo'], count[key])
        print(window, flush=True)
    (TABLES / 'h2.json').write_text(json.dumps(count, indent=1))
    (TABLES / 'verdict.json').write_text(json.dumps(dict(windows=verdicts, global_verdict='NOT_SUPPORTED' if all(v == 'NOT_SUPPORTED' for v in verdicts.values()) else 'SOME_WINDOWS_PASS', threshold=0.05 / 6, meaning='A timing pattern against the price paid and the crowd of the day. Nothing about who knew what, nor about legality, nor about what a follower could capture.'), indent=1))
    for key in count:
        enregistrer(ETUDE, test=f'H2_w{key}', declare=True, n=count[key]['observed'], agent='etude-sync', params=dict(window=int(key)), stat=count[key]['observed'] - count[key]['null_median'], p=count[key]['p'], n_tirages=count[key]['draws'], sortie='tables/h2.json')


if __name__ == '__main__':
    main()
