import chainlib as c, collections, net, labels, json
A='0x3f99139f1c5854bb628c2e576aaf638e99dffc18'
out={}
for chain,t0,t1 in ((137,'2026-10-20 00:00:00','2026-11-02 12:00:00'),(1,'2026-10-20 00:00:00','2026-11-02 12:00:00')):
    b0,b1=c.block_at(c.ts_of(t0),chain),c.block_at(c.ts_of(t1),chain)
    n=int(net.rpc('eth_getTransactionCount',[A,'latest'],chain=chain,cache=False),16)
    code=net.rpc('eth_getCode',[A,'latest'],chain=chain,cache=False)
    bal=int(net.rpc('eth_getBalance',[A,'latest'],chain=chain,cache=False),16)/1e18
    e,cut=c.all_edges(A,chain,b0,b1,cap=6000)
    out[str(chain)]=e
    print('chain',chain,'nonce',n,'code',code[:8],'bal',bal,'edges',len(e),'cut',cut,flush=True)
    ag=collections.defaultdict(lambda:[0,0.0,None,None])
    for x in e:
        k=('OUT' if x['src']==A else 'IN',x['dst'] if x['src']==A else x['src'],x['symbol'],x['token'][:10]); g=ag[k]; g[0]+=1; g[1]+=c.amount(x); g[2]=g[2] or c.utc(x['ts']); g[3]=c.utc(x['ts'])
    inn=sum(1 for k in ag if k[0]=='IN')
    print(' distinct IN keys',inn,'OUT keys',len(ag)-inn)
    for k,v in sorted(ag.items(),key=lambda kv:-kv[1][1])[:25]:
        if v[1]>0.01: print('   ',k,v[0],round(v[1],6),v[2],v[3])
    m=labels.metadata([k[1] for k in ag],chain)
    print(' tags',{k:v for k,v in m.items()})
json.dump(out,open('../state/runs/oct_core.json','w'))
