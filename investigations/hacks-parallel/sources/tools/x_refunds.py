import chainlib as c, collections, json, net, tokens, labels
R='0x71a7b22d671c93a7a40edff2ffed52dd64ed3235'
b0,b1=c.block_at(c.ts_of('2026-06-20 00:00:00')),c.block_at(c.ts_of('2026-08-15 00:00:00'))
print('nonce',int(net.rpc('eth_getTransactionCount',[R,'latest'],chain=137,cache=False),16),'code',net.rpc('eth_getCode',[R,'latest'],chain=137)[:8],labels.metadata([R],137))
rows,cut=c.history(R,137,'tokentx',b0,b1,cap=4000)
e=c.token_edges(rows,137)
print('rows',len(e),'cut',cut)
P='0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
ok=[x for x in e if x['token'] in (P,'0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359')]
for x in sorted(ok,key=lambda z:z['ts']):
    if x['src']==R and c.amount(x)>=100: print(c.utc(x['ts']),'OUT',x['dst'],x['symbol'],c.amount(x),x['tx'])
inn=collections.defaultdict(float)
for x in ok:
    if x['dst']==R: inn[(x['src'],x['symbol'])]+=c.amount(x)
print('IN',sorted(inn.items(),key=lambda kv:-kv[1])[:8])
json.dump(ok,open('../state/runs/refund_payer.json','w'))
print('total out >=100',sum(c.amount(x) for x in ok if x['src']==R and c.amount(x)>=100))
