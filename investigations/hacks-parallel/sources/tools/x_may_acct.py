import json,sys,collections
sys.path.insert(0,'.')
import chainlib as c, tokens, flows, net
ATT='0x8f98075db5d6c620e8d420a8c516e2f2059d9b91'; ADM='0x91430cad2d3975766499717fa0d66a78d814e5c5'
r=json.load(open('../state/runs/may_polygon.json'))
N=r['nodes']
E=[dict(src=e['src'],dst=e['dst'],cls=flows.asset_class(tokens.canonical_symbol(137,e)),amount=c.amount(e),ts=e['ts'],tx=e['tx'],raw=e['raw'],sym=tokens.canonical_symbol(137,e)) for e in r['edges'] if tokens.worth_following(137,e) and e['ts']<=c.ts_of('2026-07-05 00:00:00')]
inn=[e for e in r['edges'] if e['src']==ADM and e['dst']==ATT]
pol=sum(int(e['raw']) for e in inn if e['kind']!='erc20'); usd=sum(int(e['raw']) for e in inn if e['token']=='0x2791bca1f2de4661ed88a30c99a7a9449aa84174')
print('admin→attacker POL raw',pol,pol/1e18,'n',sum(e['kind']!='erc20' for e in inn),'USDC.e raw',usd,usd/1e6,'n',sum(e['token']=='0x2791bca1f2de4661ed88a30c99a7a9449aa84174' for e in inn))
print('other tokens admin→attacker',collections.Counter((e['symbol'],e['token']) for e in inn if e['kind']=='erc20' and e['token']!='0x2791bca1f2de4661ed88a30c99a7a9449aa84174'))
# USD by transfer-time price
def px(ts):
    d=net.get(f'https://coins.llama.fi/prices/historical/{ts}/coingecko:polygon-ecosystem-token,polygon:0x2791bca1f2de4661ed88a30c99a7a9449aa84174',pause=.25)['coins']
    return d['coingecko:polygon-ecosystem-token']['price'],d['polygon:0x2791bca1f2de4661ed88a30c99a7a9449aa84174']['price']
slots=sorted({e['ts']//1800*1800 for e in inn})
P={s:px(s) for s in slots}
vp=sum(c.amount(e)*P[e['ts']//1800*1800][0] for e in inn if e['kind']!='erc20'); vu=sum(c.amount(e)*P[e['ts']//1800*1800][1] for e in inn if e['token']=='0x2791bca1f2de4661ed88a30c99a7a9449aa84174')
print('USD at transfer-time: POL',round(vp,2),'USDC.e',round(vu,2),'total',round(vp+vu,2),'POL px range',min(v[0] for v in P.values()),max(v[0] for v in P.values()))
print('POL at 700k implied price',(700000-usd/1e6)/(pol/1e18))
seeds={ATT:dict(POL=pol/1e18,USD=usd/1e6)}
R=flows.propagate(E,seeds,set())
def lab(a):
    n=N.get(a,{}); return ','.join(x['name'] for x in n.get('labels',[])[:2])
out=[]
for a in set(R['poison']['got'])|set(R['poison']['left']):
    n=N.get(a,{}) 
    terminal=bool(n.get('stop') and n.get('stop')!='hop limit')
    p=R['poison']; h=R['haircut']
    pg=p['got'].get(a,{}); hg=h['got'].get(a,{}); pl=p['left'].get(a,{}); hl=h['left'].get(a,{})
    out.append((a,terminal,pg,hg,pl,hl))
print('TERMINALS and residuals (poison got/haircut got; left)')
for a,t,pg,hg,pl,hl in sorted(out,key=lambda x:-(x[2].get('USD',0)+x[2].get('POL',0)*.0925)):
    if t or pl.get('USD',0)>1 or pl.get('POL',0)>50 or hl.get('USD',0)>1 or hl.get('POL',0)>50:
        print(a,'T' if t else '-',lab(a)[:30],'nonce',N.get(a,{}).get('nonce'),'got',{k:round(v,2) for k,v in pg.items()},'hc',{k:round(v,2) for k,v in hg.items()},'left',{k:round(v,2) for k,v in pl.items()},'hcleft',{k:round(v,2) for k,v in hl.items()})
json.dump(R,open('../state/runs/may_taint.json','w'))
hubs=['0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423','0x6976d8025229db5f54bc899dd3dbc9285423896b','0x89c5151236de544d077fc69813a4db89224ee8a1']
for h in hubs:
    print(h)
    for e in sorted([e for e in E if e['dst']==h],key=lambda x:x['ts']):
        print('  ',c.utc(e['ts']),e['src'],e['sym'],e['amount'],e['tx'])
print('distinct attacker real destinations',len({e['dst'] for e in E if e['src']==ATT}))
for e in sorted([e for e in E if e['src']==ATT],key=lambda x:x['ts']): print('  ',c.utc(e['ts']),e['dst'],e['sym'],round(e['amount'],4))
