import chainlib as c, collections, net, json, labels
PUSD='0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
J='0xE42640650C634ad300a47635856AafBbBA1d2222 0xC771A30a7c1aCA828eeEF7B822ac864a64cBaAe2 0x51Cf782223289C05568F9F7Dede8CB1bC2f9c5Ca 0x10366AdBB5C4101A65C840Da6639546179C5A107 0x2eb06B8d81c6f26d9cb26327878999aC7db3891B 0xC44F2Ca6B30A54d17a62ceF8FAdaF2e8C8632eC4 0x7BCECe0d8fd92ECCf39Bc35242c6D9aAc0aA75A6 0xe65b1C586757c5510B60F998Eebb14C1eF71E1eD'.split()
J=[x.lower() for x in J]
out={}
for chain,t0,t1 in ((137,'2026-06-01 00:00:00','2026-11-02 12:00:00'),(1,'2026-06-01 00:00:00','2026-11-02 12:00:00')):
    b0,b1=c.block_at(c.ts_of(t0),chain),c.block_at(c.ts_of(t1),chain)
    print('CHAIN',chain,b0,b1)
    for a in J:
        n=int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=chain,cache=False),16)
        bal=int(net.rpc('eth_getBalance',[a,'latest'],chain=chain,cache=False),16)/1e18
        e,cut=c.all_edges(a,chain,b0,b1,cap=6000)
        out[f'{chain}:{a}']=e
        print(a,'nonce',n,'bal',round(bal,6),'edges',len(e),'cut',cut,flush=True)
        ag=collections.defaultdict(lambda:[0,0.0,None,None])
        for x in e:
            k=('OUT' if x['src']==a else 'IN',x['dst'] if x['src']==a else x['src'],x['symbol'],x['token'][:10]); g=ag[k]; g[0]+=1; g[1]+=c.amount(x); g[2]=g[2] or c.utc(x['ts']); g[3]=c.utc(x['ts'])
        for k,v in sorted(ag.items(),key=lambda kv:-kv[1][1])[:10]:
            if v[1]>0.01: print('   ',k,v[0],round(v[1],6),v[2],v[3])
json.dump(out,open('../state/runs/june_core.json','w'))
