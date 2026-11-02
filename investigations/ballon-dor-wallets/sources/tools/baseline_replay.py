"""Replays the base-rate control from the cache, for the wallets already read, and keeps every hop. Does not extend the sample. The first file is kept as it is."""
import json,sys
from pathlib import Path
sys.path.insert(0,'tools');sys.path.insert(0,'collective/code')
import baseline as B, case_chain as C, net
ROOT=Path('.')
rows=[json.loads(l) for l in open('controls/funding_baseline.jsonl')]
out=ROOT/'controls/funding_baseline_detail.jsonl'
done={json.loads(l)['wallet'] for l in out.read_text().splitlines()} if out.exists() else set()
for r in rows:
    if r['wallet'] in done or r['state']!='READ': continue
    case=C.Case('baseline')
    try:
        hop=C.trace_deposit(case,r['wallet'],dict(tx=r['deposit_tx'],at=r['at'],usd=r['usd']))
        row=dict(group=r['group'],wallet=r['wallet'],deposit_tx=r['deposit_tx'],at=r['at'],usd=r['usd'],immediate_source=(hop or {}).get('immediate_source'),immediate_kind=((hop or {}).get('kind') or {}).get('kind'),payer=((hop or {}).get('payer') or {}).get('source'),relay_user=((hop or {}).get('relay') or {}).get('user'),origin_chain=(((hop or {}).get('relay') or {}).get('in_txs') or [[None]])[0][0],hops=[dict(category=x['category'],source=x['source'],target=x['target'],chain=x['chain'],amount=x['amount'],token=x['token'],tx=x['tx'],label=(x.get('source_label') or {}).get('name'),basis=x['basis'][:120]) for x in case.relations],stops=case.stops)
    except (RuntimeError,KeyError,TypeError,ValueError,IndexError) as e:
        row=dict(group=r['group'],wallet=r['wallet'],error=str(e)[:200])
    with out.open('a') as f: f.write(json.dumps(row)+'\n')
    print(r['group'],r['wallet'][:10],row.get('immediate_source','ERR')[:10] if row.get('immediate_source') else row.get('error','none')[:60],row.get('origin_chain'),flush=True)
print('finished',net.Stats.calls,net.Stats.cached)
