import json,sys,re
sys.path.insert(0,'.')
import chainlib as c, net, es, tokens, labels, collections
SAFE='0x3dce0a29139a851da1dfca56af8e8a6440b4d952'
for h in ('0x371fbbbc774d49b25e60fc84c4667de908d6df7b4cf5d65e898c59b785c5b6b0','0xe605f22d25fddadaa1e729c63f09f4f24cdb6975bcc42d5944e4dd38b40c7d56','0x24bf4b1c9f8c7566bc3199791107dbd474313c3e8ea66000e05588af49ebc259'):
    t=net.rpc('eth_getTransactionByHash',[h],chain=137)
    rc=net.rpc('eth_getTransactionReceipt',[h],chain=137)
    json.dump(dict(tx=t,receipt=rc),open(f'../evidence/onchain/{h}.json','w'))
    raw=bytes.fromhex(t['input'][2:])
    txt=re.sub(r'[^\x20-\x7e\n]+',' ',raw.decode('latin-1'))
    print('==',h,'from',t['from'],'to',t['to'],'block',int(t['blockNumber'],16),'status',rc['status'],'len',len(raw))
    runs=[s.strip() for s in re.split(r'\s{3,}',txt) if len(s.strip())>40]
    seen=[]
    for s in runs:
        if s not in seen: seen.append(s)
    for s in seen[:6]: print('   ',s[:1400])
print('SAFE full life')
tk=es.rows('tokentx',SAFE,chain=137,offset=200)
print('recognized token rows',[(c.utc(x['timeStamp']),x['from'],x['to'],x['tokenSymbol'],int(x['value'])/10**int(x['tokenDecimal']),x['hash'][:14]) for x in tk if x['contractAddress'].lower() in tokens.RECOGNIZED[137] and int(x['value'])>0])
tx=es.rows('txlist',SAFE,chain=137,offset=400)
print('txlist n',len(tx),'2026:',[(c.utc(x['timeStamp']),x['from'][:12],x['functionName'][:24],int(x['value'])/1e18) for x in tx if int(x['timeStamp'])>c.ts_of('2026-01-01 00:00:00')][:14])
it=es.rows('txlistinternal',SAFE,chain=137,offset=400)
print('internal n',len(it),[(c.utc(x['timeStamp']),x['from'][:12],x['to'][:12],int(x['value'])/1e18,x['hash'][:12]) for x in it if int(x['timeStamp'])>c.ts_of('2025-01-01 00:00:00')][:12])
print('eth nonce',int(net.rpc('eth_getTransactionCount',[SAFE,'latest'],chain=1),16),'eth code',net.rpc('eth_getCode',[SAFE,'latest'],chain=1)[:8])
print('earlier safe activity first',[(c.utc(x['timeStamp']),x['from'][:12],x['functionName'][:30]) for x in tx[:2]])
for sign in ('0xa311aa611c','0x1890c739a7'):
    pass
print('signers seen',collections.Counter(x['from'] for x in tx if x['from'].lower()!=SAFE).most_common(8))
