import chainlib as c, collections, net, json
V='0x349606c1b77F3Ba668879CbC9347f15a44cF8fc4 0xFB84a9d631A3a19204B82c78dFeb90b220255fB5 0x4aeC70021891EA712AAf3e2dD76c30f6b09A4ce9 0x987B441a20Dd4AA4bA6d53069E852E7f820adF43 0x2d7BE5170a8026c18709EAEa1027c7f12E8Ce2Ce 0x56B4729CaE227ba1CbEb35e4d8d219f1c6fBA84b 0xa79E53B6D0893b7049cE002B279D6a6eCCA81FB0 0x5e84743aD0515699b7adF2588De4c3032d538e88'.split()
t0=c.ts_of('2026-06-24 00:00:00'); t1=c.ts_of('2026-06-27 00:00:00')
b0,b1=c.block_at(t0),c.block_at(t1)
EX='0xe2222d279d744050d28e00520010520000310f59'
dest=collections.defaultdict(lambda:[0,0.0,None,None,set()])
for v in V:
    v=v.lower()
    rows,cut=c.history(v,137,'tokentx',b0,b1,cap=4000)
    e=c.token_edges(rows,137)
    p=[x for x in e if x['token']=='0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb' and x['src']==v and x['dst']!=EX]
    big=sorted(p,key=lambda x:-c.amount(x))[:6]
    print(v,'rows',len(rows),'cut',cut,'code',net.rpc('eth_getCode',[v,'latest'],chain=137)[:8])
    for x in big: print('  ',c.utc(x['ts']),x['dst'],c.amount(x),x['tx'])
    for x in p:
        d=dest[x['dst']]; d[0]+=1; d[1]+=c.amount(x); d[2]=min(d[2],x['ts']) if d[2] else x['ts']; d[3]=x['ts']; d[4].add(v)
print('DEST')
for k,v in sorted(dest.items(),key=lambda kv:-kv[1][1])[:15]: print(k,v[0],round(v[1],2),c.utc(v[2]),c.utc(v[3]),len(v[4]))
