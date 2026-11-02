"""Registered entry point with mandatory pre-run source manifest checks."""
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from replay_core import read_rows, run_replay, kernel, CUTOFF
from registre import enregistrer
from budget import capacity, write_bytes

STUDY=Path(__file__).resolve().parents[1]

def verified_input():
    path=STUDY/'data/replay_input.jsonl.gz'
    manifest=json.loads((STUDY/'data/input_manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['input_sha256']:
        raise ValueError('Input hash differs from completed acquisition')
    rows=list(read_rows(path))
    if len(rows)!=manifest['counts']['kept']:raise ValueError('Input count differs from manifest')
    return rows

def main():
    capacity()
    rows=verified_input()
    out=STUDY/'derived/replay.json.gz';out.parent.mkdir(exist_ok=True)
    if out.exists():raise FileExistsError(out)
    last=[0.0]
    def progress(info):
        now=time.monotonic()
        if now-last[0]>=30:
            capacity()
            print(json.dumps(info),file=sys.stderr,flush=True);last[0]=now
    result=run_replay(rows,stratum='lexical_event_family_taker_only_incomplete',progress=progress)
    config=json.loads((STUDY/'code/vendor/config.json').read_text())
    strict={}
    strict_cases=kernel().evaluate(rows,[],[],now=CUTOFF-1,config=config,diagnostics=strict)
    result['strict_actual_observation_replay']=dict(diagnostics=strict,cases=len(strict_cases),
        meaning='Absent contemporaneous observations; not a historical sensitivity estimate')
    result['n_comparisons']+=1
    write_bytes(out,gzip.compress(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    enregistrer(str(STUDY),test='R1_conditional_blind_chronological_replay',declare=True,n=len(rows),
                n_effectif=1,n_comparaisons=result['n_comparisons'],agent='blind-replay-implementation',
                sortie='derived/replay.json.gz',params={'delays':[0,60,300,900],'no_public_labels':True},
                note='Conditional reconstructed availability and eligibility, not real historical alert emission; native thresholds unchanged')
    print(json.dumps(dict(output=str(out),n_comparisons=result['n_comparisons'])))

if __name__=='__main__':main()
