import chainlib as c, collections, net, json
ADM='0x91430cad2d3975766499717fa0d66a78d814e5c5'; ATT='0x8f98075db5d6c620e8d420a8c516e2f2059d9b91'
A871='0x871d7c0f9e19001fc01e04e6cdfa7fa20f929082'; F61='0xf61e39c7eb1e2ff5af3a24bca88d40fd11594805'; GAS='0xff4c483c4c7f72f78077527521fce4b2595e454f'
b0=c.block_at(c.ts_of('2026-05-15 00:00:00')); b1=c.block_at(c.ts_of('2026-07-05 00:00:00'))
# nonce proof around 14 June
for label,ts in (('06-13 23:59',c.ts_of('2026-06-13 23:59:59')),('06-15 00:00',c.ts_of('2026-06-15 00:00:00')),('05-22 05:00',c.ts_of('2026-05-22 05:00:00')),('05-22 12:00',c.ts_of('2026-05-22 12:00:00')),('06-19 00:00',c.ts_of('2026-06-19 00:00:00')),('06-20 00:00',c.ts_of('2026-06-20 00:00:00'))):
    b=c.block_at(ts)
    row=[label,b]
    for a in (ADM,A871,F61,ATT,GAS):
        try:
            row.append(int(net.rpc('eth_getTransactionCount',[a,hex(b)],chain=137),16))
        except Exception as e:
            row.append('ERR '+str(e)[:70])
    print(row,flush=True)
e,_=c.all_edges(ADM,137,b0,b1)
print('admin edges',len(e))
day=[x for x in e if x['ts']>=c.ts_of('2026-05-22 00:00:00')]
inn=[x for x in day if x['dst']==ADM]
agg=collections.defaultdict(lambda:[0,0.0,None,None])
for x in inn:
    k=(x['src'],x['symbol'],x['token'][:10]); agg[k][0]+=1; agg[k][1]+=c.amount(x); agg[k][2]=agg[k][2] or c.utc(x['ts']); agg[k][3]=c.utc(x['ts'])
print('IN to admin since 05-22'); [print(' ',k,v) for k,v in sorted(agg.items(),key=lambda kv:-kv[1][1])[:14]]
out=[x for x in day if x['src']==ADM]
agg=collections.defaultdict(lambda:[0,0.0,None,None])
for x in out:
    k=(x['dst'],x['symbol'],x['token'][:10]); agg[k][0]+=1; agg[k][1]+=c.amount(x); agg[k][2]=agg[k][2] or c.utc(x['ts']); agg[k][3]=c.utc(x['ts'])
print('OUT of admin since 05-22'); [print(' ',k,v) for k,v in sorted(agg.items(),key=lambda kv:-kv[1][1])[:14]]
# last ordinary out before attacker, first attacker
ord_=[x for x in out if x['dst']!=ATT and x['ts']<c.ts_of('2026-05-22 12:00:00')]
print('last ordinary out',c.utc(ord_[-1]['ts']) if ord_ else None, ord_[-1]['dst'] if ord_ else None)
att=[x for x in out if x['dst']==ATT]; print('attacker first/last',c.utc(att[0]['ts']),att[0]['tx'],c.utc(att[-1]['ts']),att[-1]['tx'])
for a,name in ((A871,'871d'),(F61,'f61e'),(GAS,'gasfunder')):
    n=int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137,cache=False),16)
    ee,cut=c.all_edges(a,137,c.block_at(c.ts_of('2026-05-20 00:00:00')),b1,cap=6000)
    print(name,a,'nonce',n,'edges',len(ee),'cut',cut,'code',net.rpc('eth_getCode',[a,'latest'],chain=137,cache=False)[:6])
    dd=collections.Counter((c.utc(x['ts'])[:10],'out' if x['src']==a else 'in') for x in ee)
    print('  days',sorted(dd.items())[:30])
    ag=collections.defaultdict(lambda:[0,0.0,None,None])
    for x in ee:
        k=('OUT' if x['src']==a else 'IN', x['dst'] if x['src']==a else x['src'], x['symbol'], x['token'][:10]); ag[k][0]+=1; ag[k][1]+=c.amount(x); ag[k][2]=ag[k][2] or c.utc(x['ts']); ag[k][3]=c.utc(x['ts'])
    for k,v in sorted(ag.items(),key=lambda kv:-kv[1][1])[:12]: print('   ',k,v)
