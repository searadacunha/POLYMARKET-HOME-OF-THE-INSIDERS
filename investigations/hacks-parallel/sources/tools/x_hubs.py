import chainlib as c, collections, net, labels, json, tokens
H={'0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423':'f2020','0x6976d8025229db5f54bc899dd3dbc9285423896b':'6976','0x89c5151236de544d077fc69813a4db89224ee8a1':'89c5'}
t0=c.ts_of('2026-05-21 00:00:00'); t1=c.ts_of('2026-05-24 00:00:00'); b0,b1=c.block_at(t0),c.block_at(t1)
for a,n in H.items():
    print('==',n,a,'nonce',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137),16),'eth nonce',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=1),16),'bal',int(net.rpc('eth_getBalance',[a,'latest'],chain=137),16)/1e18,flush=True)
    e,cut=c.all_edges(a,137,b0,b1,cap=8000)
    e=[x for x in e if tokens.recognized(137,x) and t0<=x['ts']<t1]
    print(' edges',len(e),'cut',cut,'span',c.utc(min(x['ts'] for x in e)),c.utc(max(x['ts'] for x in e)))
    for side,key in (('IN','src'),('OUT','dst')):
        rows=[x for x in e if (x['dst'] if side=='IN' else x['src'])==a]
        by=collections.defaultdict(lambda:collections.defaultdict(float)); cnt=collections.Counter()
        for x in rows:
            by[x[key]][tokens.canonical_symbol(137,x)]+=c.amount(x); cnt[x[key]]+=1
        tot=collections.defaultdict(float)
        for k,v in by.items():
            for s,q in v.items(): tot[s]+=q
        print(' ',side,'rows',len(rows),'distinct',len(by),'once',sum(1 for k in cnt if cnt[k]==1),'totals',{s:round(q,2) for s,q in tot.items()})
        def score(k): return by[k].get('USDC.e',0)+by[k].get('USDC',0)+by[k].get('USDT',0)+by[k].get('POL',0)*.09
        top=sorted(by,key=lambda k:-score(k))[:12]
        m=labels.metadata(top,137)
        for k in top: print('    ',k,cnt[k],{s:round(q,2) for s,q in by[k].items()},[x['name'] for x in labels.lookup(k,137,m)][:3])
