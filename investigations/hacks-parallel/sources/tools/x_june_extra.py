"""June extras: Relay's own record of each Polygon deposit by the staging wallets, and refunds received by the 14 accounts."""
import chainlib as c, collections, json, net, es, tokens
PUSD='0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
DEPOSITORY='0x4cd00e387622c35bddb9b4c962c136462338bc31'
d=json.load(open('../state/runs/june_core.json'))
S={k.split(':')[1] for k in d if k.startswith('137:')}
dep=[x for k,es_ in d.items() if k.startswith('137:') for x in es_ if x['dst']==DEPOSITORY and c.amount(x)>=100 and x['token'] and tokens.recognized(137,x)]
seen=set(); relay={}
for x in dep:
    if x['tx'] in seen: continue
    seen.add(x['tx'])
    r=net.get('https://api.relay.link/requests/v2',dict(hash=x['tx']),pause=.5)
    relay[x['tx']]=dict(from_=x['src'],amount=c.amount(x),ts=x['ts'],requests=r.get('requests') or [])
    q=relay[x['tx']]['requests']
    if q:
        m=q[0]; dd=m.get('data',{}); inn=(dd.get('inTxs') or [{}])[0]; ou=(dd.get('outTxs') or [{}])[0]
        print(c.utc(x['ts']),x['src'][:10],round(c.amount(x),2),'→ chain',ou.get('chainId'),ou.get('hash'),'status',m.get('status'),'user',m.get('user'),'recipient',m.get('recipient'),flush=True)
    else:
        print(c.utc(x['ts']),x['src'][:10],round(c.amount(x),2),'NO RELAY RECORD',flush=True)
json.dump(relay,open('../state/runs/relay_june.json','w'))
V=[('0xb61b2079b95f6b7476fd3203e0274ffb93308a06',1094606.657825),('0x987b441a20dd4aa4ba6d53069e852e7f820adf43',508517.990186),('0xd88139efbecc8641892e17171afcced35315af24',446538.67362),('0x2d7be5170a8026c18709eaea1027c7f12e8ce2ce',343997.546264),('0x08a30a0a0fb71ebddc8907145791030782b88666',247993.249107),('0x56b4729cae227ba1cbeb35e4d8d219f1c6fba84b',202433.636082),('0x79ae097215202b5d01f98e4479fb219102469a4a',143033.286322),('0x349606c1b77f3ba668879cbc9347f15a44cf8fc4',36560.878495),('0x5f659bccbc353dbf7bcdffdee73bee60bb482036',32711.399497),('0x4aec70021891ea712aaf3e2dd76c30f6b09a4ce9',27142.227527),('0x92ee6583b495d71a33cc9b73f4f7ddf8ff8f90e6',25034.404822),('0xfb84a9d631a3a19204b82c78dfeb90b220255fb5',2403.930799),('0x5e84743ad0515699b7adf2588de4c3032d538e88',2032.016479),('0xa79e53b6d0893b7049ce002b279d6a6ecca81fb0',209.318709)]
b0,b1=c.block_at(c.ts_of('2026-06-25 05:00:00')),c.block_at(c.ts_of('2026-07-31 00:00:00'))
ref={}
for v,lost in V:
    rows=[]
    cursor=b0
    for _ in range(6):
        p=es.rows('tokentx',v,chain=137,start=cursor,end=b1,offset=1000,contract=PUSD)
        rows+=p
        if len(p)<1000: break
        cursor=int(p[-1]['blockNumber'])
    inn=[r for r in rows if r['to'].lower()==v]
    near=[r for r in inn if abs(int(r['value'])/1e6-lost)<=max(lost*.05,50)]
    send=collections.Counter(r['from'].lower() for r in inn if int(r['value'])/1e6>=max(lost*.3,100))
    ref[v]=dict(lost=lost,near=[dict(ts=c.utc(r['timeStamp']),src=r['from'],amount=int(r['value'])/1e6,tx=r['hash']) for r in near],large_senders=send.most_common(4),rows=len(rows))
    print(v[:10],lost,'rows',len(rows),'near',[(x['ts'],x['src'][:10],x['amount']) for x in ref[v]['near']][:3],'large',send.most_common(2),flush=True)
json.dump(ref,open('../state/runs/refunds_june.json','w'))
