"""Audit, offline: relations, money and shared addresses recomputed from the case files. Reads only."""
import glob,itertools,json,os,re,statistics,sys
from collections import Counter,defaultdict
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
print('relations',len(rel),'unique ids',len({r['id'] for r in rel}))
print('by category',Counter(r['category'] for r in rel))
print('by case',dict(Counter(r['case'] for r in rel)))
print('by chain',Counter(r['chain'] for r in rel))
embedded={r['id'] for c in cases.values() for r in c.get('chain_relations',[])}
print('in graph not in cases',len({r['id'] for r in rel}-embedded),'in cases not in graph',len(embedded-{r['id'] for r in rel}))
same=sum(1 for c in cases.values() for r in c['chain_relations'] if r not in rel)
print('case copies differing from graph',same)
z='0x'+'0'*40
print('zero address as target/source',sum(r['target']==z for r in rel),sum(r['source']==z for r in rel))
print('no tx',Counter((r['category'],r['basis'][:40]) for r in rel if not r['tx']))
ownership=Counter(r['ownership'] for r in rel);print('ownership field',ownership)
key=Counter((str(r['tx']),r['log_index'],str(r['source']).lower(),str(r['target']).lower()) for r in rel if r['tx'])
print('same tx+log+ends repeated',sum(1 for v in key.values() if v>1),[k for k,v in key.items() if v>1][:6])
across=defaultdict(set)
for r in rel:
    if r['tx']: across[r['tx'].lower()].add(r['case'])
print('tx appearing in two cases',{k:sorted(v) for k,v in across.items() if len(v)>1})
print('\n=== 25 withdrawals against relations')
tot=0;n=0;miss=[]
txs=Counter()
for s,c in cases.items():
    for w in c['withdrawals']:
        n+=1;tot+=w['usd'];txs[w['tx'].lower()]+=1
        rs=[r for r in c['chain_relations'] if (r.get('payout_tx') or '').lower()==w['tx'].lower() or (r.get('tx') or '').lower()==w['tx'].lower()]
        if len(rs)!=1: miss.append((s,w['tx'][:12],len(rs),[x['category'] for x in rs]))
        for r in rs:
            if r['received'] is not None and abs(r['received']-w['usd'])>.01: print(' received differs',s,w['usd'],r['received'])
print('withdrawals',n,'sum',round(tot,2),'dup tx',[k for k,v in txs.items() if v>1],'not exactly one relation',miss)
print('deposits',sum(len(c['deposits']) for c in cases.values()),'sum',round(sum(d['usd'] for c in cases.values() for d in c['deposits']),2),'dup',[k for k,v in Counter(d['tx'].lower() for c in cases.values() for d in c['deposits']).items() if v>1])
print('tx both deposit and withdrawal',set(d['tx'].lower() for c in cases.values() for d in c['deposits'])&set(txs))
print('\n=== settled perimeter')
closed={s:c['account']['net_cash_out_minus_in'] for s,c in cases.items() if c['account']['account_closed']}
print('closed',len(closed),'sum',round(sum(closed.values()),2))
rows=[]
for s,c in cases.items():
    a=c['account'];pusd=(c['balances_now'].get('pUSD') or 0)/1e6
    rows.append((s,round(a['withdrawals']-a['deposits'],2),a['account_closed'],a['residual'],round(pusd,4),round(a['residual']-pusd,4),a['unknown_types'],c['open_positions']['open_rows'],c['open_positions']['current_value']))
    print(rows[-1])
print('all 11, withdrawals minus deposits',round(sum(r[1] for r in rows),2),'not closed',[(r[0],r[1]) for r in rows if not r[2]])
print('by_type totals',{k:round(sum(c['account']['by_type'].get(k,0) for c in cases.values()),2) for k in ('DEPOSIT','WITHDRAWAL','TRADE_BUY','TRADE_SELL','REDEEM','REWARD','MAKER_REBATE','TAKER_REBATE')})
print('\n=== shared addresses recomputed from relations + hops')
own={c['address'].lower():s for s,c in cases.items()}
seen=defaultdict(lambda:defaultdict(set))
for r in rel:
    for side in('source','target'):
        a=r[side]
        if not a:continue
        a2=a.lower() if a.startswith('0x') else a
        if a2==z: continue
        seen[a2][r['case']].add(r['chain'])
shared={a:v for a,v in seen.items() if len(v)>1}
nodes=json.load(open(I+'graphs/links_classified.json'))
classified={(n['address'].lower() if n['address'].startswith('0x') else n['address']):n for n in nodes['nodes']}
for a,v in sorted(shared.items(),key=lambda x:-len(x[1])):
    print(a[:14],sorted(v),'classified' if a in classified else 'NOT CLASSIFIED',classified.get(a,{}).get('class_',''))
print('classified but not shared in relations',[a[:14] for a in classified if a not in shared])
pairs=set()
for a,v in shared.items():
    pairs|=set(itertools.combinations(sorted(v),2))
print('pairs from any shared address',len(pairs),'reported',nodes['naive_pair_count'],'possible',nodes['possible_pairs'],'discriminant',nodes['discriminant_nodes'],nodes['discriminant_pairs'])
pc=set()
for n in nodes['nodes']:pc|=set(itertools.combinations(sorted(n['cases']),2))
print('pairs from classified nodes',len(pc))
print('\n=== classification')
for n in nodes['nodes']:print(n['address'][:12],n['class_'],n['cases'],'|',n['why'][:230],'| baseline',n.get('also_in_baseline'))
print('direct_funds',nodes.get('direct_funds_across_cases'),'clob',nodes.get('clob_matches'))
print('\n=== timing of the main withdrawal per wallet')
ev=[]
for s,c in cases.items():
    big=max(c['withdrawals'],key=lambda w:w['usd']);first=min((w for w in c['withdrawals'] if w['usd']>=100),key=lambda w:w['at'])
    ev.append((big['at'],s,big['usd'],big['utc']))
for e in sorted(ev):print(e[3],e[1],round(e[2],2))
ts=sorted(e[0] for e in ev);print('gaps min',[round((b-a)/60,1) for a,b in zip(ts,ts[1:])])
print('\n=== routes per case')
for s,c in cases.items():
    print(s,'key',c['wallet'].get('owners'),'dep chains',[ (h or {}).get('relay',{}).get('in_txs',[[None]])[0][0] if (h or {}).get('relay') else None for h in c['funding_chain']],'exits',[(h.get('out_chain'),str(h.get('recipient'))[:10]) for h in c['exit_chain']],'stops',len(c['chain_stops']))
