import chainlib as c, collections, net, labels, json, tokens
ST=c.ts_of('2026-05-20 00:00:00'); EN=c.ts_of('2026-11-02 12:00:00')
b0,b1=c.block_at(ST),c.block_at(EN)
HUBS={'0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423','0x6976d8025229db5f54bc899dd3dbc9285423896b','0x89c5151236de544d077fc69813a4db89224ee8a1','0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a'}
for a,n in (('0x2d507657ca4ebcc8f9a38f6764c07310b66dea54','treasury'),('0xf43d55f3a8b7484ed4b6931f93cb6f9ef5dd369d','newadmin')):
    cap=3000 if n=='newadmin' else None
    e,cut=c.all_edges(a,137,b0,b1 if n!='newadmin' else c.block_at(c.ts_of('2026-05-25 00:00:00')),cap=cap)
    e=[x for x in e if tokens.recognized(137,x)]
    print('==',n,a,'edges',len(e),'cut',cut, 'first',c.utc(min(x['ts'] for x in e)) if e else None)
    ag=collections.defaultdict(lambda:[0,0.0,None,None])
    for x in e:
        k=('OUT' if x['src']==a else 'IN',x['dst'] if x['src']==a else x['src'],tokens.canonical_symbol(137,x)); g=ag[k]; g[0]+=1; g[1]+=c.amount(x); g[2]=g[2] or c.utc(x['ts']); g[3]=c.utc(x['ts'])
    top=sorted(ag.items(),key=lambda kv:-kv[1][1])[:18]
    m=labels.metadata([k[1] for k,_ in top],137)
    for k,v in top: print('   ',k,v[0],round(v[1],4),v[2],v[3],[x['name'] for x in labels.lookup(k[1],137,m)][:2])
    print(' inflows from hubs:',[ (k,v[:2]) for k,v in ag.items() if k[0]=='IN' and k[1] in HUBS])
# June 14 test on every Polymarket wallet named in the May case
day0=c.ts_of('2026-06-14 00:00:00'); day1=c.ts_of('2026-06-15 00:00:00')
for a,n in (('0x91430cad2d3975766499717fa0d66a78d814e5c5','admin'),('0x871d7c0f9e19001fc01e04e6cdfa7fa20f929082','871d'),('0xf61e39c7eb1e2ff5af3a24bca88d40fd11594805','f61e'),('0x2d507657ca4ebcc8f9a38f6764c07310b66dea54','treasury'),('0x8f98075db5d6c620e8d420a8c516e2f2059d9b91','attacker'),('0xff4c483c4c7f72f78077527521fce4b2595e454f','gasfunder')):
    e,_=c.all_edges(a,137,c.block_at(day0),c.block_at(day1))
    e=[x for x in e if tokens.recognized(137,x) and day0<=x['ts']<day1]
    o=[x for x in e if x['src']==a]
    print('06-14',n,'out',len(o),[(c.utc(x['ts'])[11:16],x['dst'][:10],round(c.amount(x),2),tokens.canonical_symbol(137,x)) for x in o][:14],'in',len(e)-len(o))
print('admin first activity',)
tx=c.es.rows('txlist','0x91430cad2d3975766499717fa0d66a78d814e5c5',chain=137,offset=3)
print([(c.utc(r['timeStamp']),r['hash'],r['from'],r['to'],int(r['value'])/1e18) for r in tx])
tk=c.es.rows('tokentx','0x91430cad2d3975766499717fa0d66a78d814e5c5',chain=137,offset=2)
print([(c.utc(r['timeStamp']),r['hash'],r['from'],r['tokenSymbol'],int(r['value'])/10**int(r['tokenDecimal'])) for r in tk])
tx=c.es.rows('txlist','0xff4c483c4c7f72f78077527521fce4b2595e454f',chain=137,offset=4)
print('funder first',[(c.utc(r['timeStamp']),r['hash'],r['from'],r['to'],r['functionName'][:40]) for r in tx])
