import chainlib as c, net, labels, tokens, collections, json, itertools
USDCE='0x2791bca1f2de4661ed88a30c99a7a9449aa84174'
def bal(token,a):
    return int(net.rpc('eth_call',[dict(to=token,data='0x70a08231'+'0'*24+a[2:]),'latest'],chain=137,cache=False),16)
print('PARKED now (POL, USDC.e)')
for a in ('0xdd5535163619aeae882532a9a6393d18a309fff7','0x0a804f680640be6228d4ce0d73c8f5fb5f9a2e68','0x0fb2f44ecad0d1b798a7317629acb85a7fcdcad8','0xca07efe820838bfc70f489a60eed9cb09c4cfd76','0x2ed3e9cc75aa5a2e7d7f4b2f006a2e0fd08e7e04','0x6d1f3eea4f5f2b37239608486877ca4e582f2974'):
    print(a,round(int(net.rpc('eth_getBalance',[a,'latest'],chain=137,cache=False),16)/1e18,4),bal(USDCE,a)/1e6,'nonce',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137,cache=False),16))
print('EXITS of 0x89c5 path')
b0,b1=c.block_at(c.ts_of('2026-05-22 00:00:00')),c.block_at(c.ts_of('2026-11-02 12:00:00'))
for a in ('0x3dce0a29139a851da1dfca56af8e8a6440b4d952','0x682c9c6643c6552185b3d6e796fbe2e40b34cb35','0x61de7407ed37e58d2372bec6d1b786fa21050f1b','0x7509d2f9a125de221e84375bab360c1c9c549397'):
    m=labels.metadata([a],137)
    n=int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137,cache=False),16)
    print(a,'nonce',n,[x['name'] for x in labels.lookup(a,137,m)][:3],'code',net.rpc('eth_getCode',[a,'latest'],chain=137)[:6])
    if n>=2000: continue
    e,cut=c.all_edges(a,137,b0,b1,cap=1500)
    e=[x for x in e if tokens.worth_following(137,x)]
    ag=collections.defaultdict(lambda:[0,0.0,None])
    for x in e:
        k=('OUT' if x['src']==a else 'IN',x['dst'] if x['src']==a else x['src'],tokens.canonical_symbol(137,x)); g=ag[k]; g[0]+=1; g[1]+=c.amount(x); g[2]=g[2] or c.utc(x['ts'])
    top=sorted(ag.items(),key=lambda kv:-kv[1][1])[:7]
    mm=labels.metadata([k[1] for k,_ in top],137)
    for k,v in top: print('    ',k[0],k[1],k[2],v[0],round(v[1],2),v[2],[x['name'] for x in labels.lookup(k[1],137,mm)][:2])
print('Gas helper 0x0e2ea4d1')
g='0x0e2ea4d1ae07cf636e6fdde4ac89891f9dd63e2b'
print(int(net.rpc('eth_getTransactionCount',[g,'latest'],chain=137,cache=False),16),labels.metadata([g],137))
