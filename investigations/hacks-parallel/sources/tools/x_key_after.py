import chainlib as c, collections, net, labels, es, json
ADM='0x91430cad2d3975766499717fa0d66a78d814e5c5'; G='0xff4c483c4c7f72f78077527521fce4b2595e454f'
b0=c.block_at(c.ts_of('2026-05-22 12:00:00')); b1=c.block_at(c.ts_of('2026-11-02 12:00:00'))
tx,_=c.history(ADM,137,'txlist',b0,b1)
out=[r for r in tx if r['from'].lower()==ADM]
print('admin outgoing after 05-22 12:00:',len(out))
ts=sorted({r['to'].lower() for r in out if r['to']}); m=labels.metadata(ts,137)
for r in out:
    print(c.utc(r['timeStamp']),r['hash'],'→',r['to'],[y['name'] for y in labels.lookup(r['to'],137,m)][:2],int(r['value'])/1e18,'err' if r['isError']!='0' else 'ok',r['methodId'],r['functionName'][:48],'|',r['input'][10:10+64*2][:128])
print('admin in after',[(c.utc(r['timeStamp']),r['from'][:12],int(r['value'])/1e18) for r in tx if r['to'].lower()==ADM][:6])
for a in ('0x6656680f7992c6dab0975ef7bdaf4693a24519ee','0x7b83d2b5bca3b52c75651369c1cd926ff52aa651'):
    e,_=c.all_edges(a,137,c.block_at(c.ts_of('2026-06-01 00:00:00')),b1,cap=800)
    e=[x for x in e if int(x['raw'])>0 and (x['kind']!='erc20' or x['token'] in ('0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0xc2132d05d31c914a87c6611c10748aeb04b58e8f'))]
    print(a,len(e)); [print('  ',c.utc(x['ts']),'OUT' if x['src']==a else 'IN',x['dst'] if x['src']==a else x['src'],x['symbol'],round(c.amount(x),4)) for x in e[:12]]
gx,_=c.history(G,137,'txlist',0,99999999)
print('funder rows',len(gx),'first',c.utc(gx[0]['timeStamp']),'last',c.utc(gx[-1]['timeStamp']))
to=collections.Counter((r['to'] or '').lower() for r in gx if r['from'].lower()==G)
m=labels.metadata(list(to),137)
for a,n in to.most_common(8): print('  to',a,n,[y['name'] for y in labels.lookup(a,137,m)][:2],collections.Counter(r['functionName'][:28] for r in gx if (r['to'] or '').lower()==a).most_common(3))
print('  by month',sorted(collections.Counter(c.utc(r['timeStamp'])[:7] for r in gx if r['from'].lower()==G).items()))
inn=[r for r in gx if r['to'].lower()==G and int(r['value'])>0]
print('  funded by',collections.Counter(r['from'][:12] for r in inn).most_common(6),'POL in',sum(int(r['value']) for r in inn)/1e18)
print('  first in',[(c.utc(r['timeStamp']),r['from'],round(int(r['value'])/1e18,3)) for r in inn[:3]])
