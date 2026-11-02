import json,sys,collections
sys.path.insert(0,'.')
import chainlib as c, tokens, flows
E0='0xe65b1c586757c5510b60f998eebb14c1ef71e1ed'
r=json.load(open('../state/runs/june_eth.json'))
N=r['nodes']; print('nodes',len(N),'edges',len(r['edges']),'unread',len(r['unread']))
print('kinds',collections.Counter(n.get('stop','') .split(' ')[0] for n in N.values()).most_common(8))
core=json.load(open('../state/runs/june_core.json'))
inn=[x for x in core['1:'+E0] if x['kind']!='erc20' and x['dst']==E0 and c.amount(x)>=1]
eth=sum(int(x['raw']) for x in inn)/1e18
print('into consolidation',eth,len(inn))
E=[dict(src=e['src'],dst=e['dst'],cls=flows.asset_class(tokens.canonical_symbol(1,e)),amount=c.amount(e),ts=e['ts'],tx=e['tx']) for e in r['edges'] if tokens.worth_following(1,e) and e['dst']!=E0]
R=flows.propagate(E,{E0:dict(ETH=eth)},set())
json.dump(R,open('../state/runs/june_taint.json','w'))
rows=[]
for a in set(R['poison']['left'])|set(R['haircut']['left']):
    pl=R['poison']['left'].get(a,{}); hl=R['haircut']['left'].get(a,{})
    if pl.get('ETH',0)<.5 and hl.get('ETH',0)<.5: continue
    n=N.get(a,{}); rows.append((pl.get('ETH',0),hl.get('ETH',0),a,n.get('kind'),n.get('nonce'),(n.get('stop') or '')[:16],[x['name'] for x in n.get('labels',[])][:2]))
rows.sort(key=lambda x:-x[0])
print('ETH left poison',round(sum(v.get('ETH',0) for v in R['poison']['left'].values()),3),'haircut',round(sum(v.get('ETH',0) for v in R['haircut']['left'].values()),3))
for x in rows[:32]: print(round(x[0],3),round(x[1],3),*x[2:])
print('touch changenow?',[a for a,n in N.items() if any('change' in y['name'].lower() for y in n.get('labels',[]))][:10])
print('direct edges to studied CN',[(c.utc(e['ts']),e['src'][:12],e['dst'][:12],round(c.amount(e),4)) for e in r['edges'] if e['dst'] in ('0xdd3d72c53ff982ff59853da71158bf1538b3ceee','0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b','0xeba88149813bec1cccccfdb0dacefaaa5de94cb1')][:10])
