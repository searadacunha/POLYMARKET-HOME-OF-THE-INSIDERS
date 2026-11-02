"""Second hop: recipients of real value from the keys, never read before. Writes state/hop2.json."""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es
ROOT = Path(__file__).resolve().parent.parent
targets = [t for t in json.load(open(ROOT / 'state/hop2_targets.json')) if t['from_key']]
extra = [dict(address='0x3eaef6d5e91ecf7b7623eb19978e145ebd417013', chain=1, cases=['brace227'], from_key=False, kinds=['funder'], n=0, senders=[])]
res = []
for t in targets + extra:
    a, c = t['address'], t['chain']
    tx = es.rows('txlist', a, c)
    tk = es.rows('tokentx', a, c)
    it = es.rows('txlistinternal', a, c)
    outs = [r for r in tx if r['from'].lower() == a and int(r['value']) > 0] + [r for r in tk if r['from'].lower() == a]
    ins = [r for r in tx if r['to'].lower() == a and int(r['value']) > 0] + [r for r in tk if r['to'].lower() == a] + [r for r in it if r['to'].lower() == a and int(r['value']) > 0]
    res.append(dict(t, tx=len(tx), tokens=len(tk), internal=len(it), sent=sum(r['from'].lower() == a for r in tx), capped=len(tx) >= 1000 or len(tk) >= 1000, top_out=Counter(r['to'].lower() for r in outs).most_common(8), top_in=Counter(r['from'].lower() for r in ins).most_common(8), rows_tx=tx[:40], rows_tk=tk[:60]))
    print(a, c, t['cases'], 'tx', len(tx), 'tok', len(tk), 'int', len(it), 'sent', res[-1]['sent'], 'out', res[-1]['top_out'][:3], flush=True)
(ROOT / 'state/hop2.json').write_text(json.dumps(res))
