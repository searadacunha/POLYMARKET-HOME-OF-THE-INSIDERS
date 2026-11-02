import chainlib as c, collections, net, labels, json, sys
ATT='0x8f98075db5d6c620e8d420a8c516e2f2059d9b91'
b0=c.block_at(c.ts_of('2026-05-22 00:00:00')); b1=c.block_at(c.ts_of('2026-07-05 00:00:00'))
D=['0x4b20080924b4b999676cf85748fe564a6137edd2','0xe696cadce07b6be114d19b98c1e8d423c741a7ea','0x8c4d25d0cf9ce62053bbb6d04fb8bd7812e23ed5','0xd7d6a0e2b92d2ac2168b807d3a5436b3006e4c63','0x47b7c11bc90bd767c0f464082236119b9d8a7518','0xca310141c53eda70e8fbb15371f8000971087222','0xbe311a69cdfb515a116e5dce13eadf21c4b3fd53','0xe03fd8672d017c97c0d83957532e81979570c3d4','0xc49531cd02ab5a04b813b0467400461837a6f3b4','0x6d1f3eea4f5f2b37239608486877ca4e582f2974','0x74d1cbd70fdb3b8f60bf56353c94deaa5cf30be6','0x6e01404037245d8446fcc5c15b3cf1e035710658','0xbcbba9672f362f49635efb8d756c19d181a1837e','0xc9be3ddc780e622d640bb770a1fd8834d8f269c8','0xa1f095be77bbd6457e275d9f061478ed467a189b','0xfc7ab92afb03cab54c1587f68296689ce5c20453','0xd3cfcd214eb51b70627c3d78e0c22e1479880e9e']
for a in D:
    n=int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137,cache=False),16)
    code=net.rpc('eth_getCode',[a,'latest'],chain=137,cache=False)
    e,cut=c.all_edges(a,137,b0,b1,cap=3000)
    inn=[x for x in e if x['dst']==a]; out=[x for x in e if x['src']==a]
    def agg(rows,key):
        d=collections.defaultdict(lambda:[0,0.0,None])
        for x in rows:
            k=(x[key],x['symbol'],x['token'][:8])
            d[k][0]+=1; d[k][1]+=c.amount(x); d[k][2]=d[k][2] or c.utc(x['ts'])
        return sorted(d.items(),key=lambda kv:-kv[1][1])[:5]
    print(a,'nonce',n,'code',len(code)>2,'cut',cut,'in',len(inn),'out',len(out))
    print('   IN ',[(k[0],k[1],v[0],round(v[1],2),v[2]) for k,v in agg(inn,'src')])
    print('   OUT',[(k[0],k[1],v[0],round(v[1],2),v[2]) for k,v in agg(out,'dst')])
