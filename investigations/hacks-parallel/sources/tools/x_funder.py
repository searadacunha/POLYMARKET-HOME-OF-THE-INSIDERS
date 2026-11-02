import chainlib as c, collections, net, labels, es, json
G='0xff4c483c4c7f72f78077527521fce4b2595e454f'
gx,_=c.history(G,137,'txlist',0,99999999)
tf=[r for r in gx if r['methodId']=='0x23b872dd']
print('transferFrom calls',len(tf))
agg=collections.defaultdict(lambda:[0,0,None,None,0])
for r in tf:
    i=r['input']; src='0x'+i[10+24:10+64]; dst='0x'+i[10+64+24:10+128]; v=int(i[10+128:10+192],16)
    g=agg[(src,dst)]; g[0]+=1; g[1]+=v; g[2]=g[2] or c.utc(r['timeStamp']); g[3]=c.utc(r['timeStamp']); g[4]+=r['isError']!='0'
for k,v in sorted(agg.items(),key=lambda kv:-kv[1][1]): print(k,v[0],v[1]/1e6,v[2],v[3],'failed',v[4])
m=labels.metadata(list({a for k in agg for a in k}),137); print({a:[y['name'] for y in labels.lookup(a,137,m)][:2] for a in {a for k in agg for a in k}})
oth=[r for r in gx if r['from'].lower()==G and r['to'].lower() in ('0xea5938d591a0059f9b5a845d955aedabb1283518','0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e','0x4d97dcd97ec945f40cf65f87097ace5ea0476045')]
for r in oth: print(c.utc(r['timeStamp']),r['hash'][:14],r['to'][:10],r['functionName'][:30],int(r['value'])/1e18,r['isError'])
tk=es.rows('tokentx',G,chain=137,offset=200)
ag=collections.defaultdict(lambda:[0,0.0,None,None])
for x in tk:
    if x['contractAddress'].lower() not in ('0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'): continue
    if x['from'].lower()==G: k=('OUT',x['to'].lower(),x['tokenSymbol'])
    else: k=('IN',x['from'].lower(),x['tokenSymbol'])
    g=ag[k]; g[0]+=1; g[1]+=int(x['value'])/1e6; g[2]=g[2] or c.utc(x['timeStamp']); g[3]=c.utc(x['timeStamp'])
print('stable rows',len(tk))
for k,v in sorted(ag.items(),key=lambda kv:-kv[1][1])[:12]: print(k,v[0],round(v[1],2),v[2],v[3])
for a in ('0xc0126535cbc6f70fc71d41bbc266d76321159efe','0x8669debfa2b60f73300a95140b02408263cece01'):
    print(a,'nonce',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137),16),labels.metadata([a],137))
    t=es.rows('txlist',a,chain=137,offset=8); print('   first',[(c.utc(r['timeStamp']),r['from'][:10],(r['to'] or '')[:10],round(int(r['value'])/1e18,2),r['functionName'][:18]) for r in t][:8])
