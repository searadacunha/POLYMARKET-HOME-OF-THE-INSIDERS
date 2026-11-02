import json,collections,datetime as dt,sys
from lab import label
T='0x3b6dcfde35e53fb7dca8571f23286631b5123c5b'
OFF={1:{'0xdac17f958d2ee523a2206206994597c13d831ec7':'USDT','0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'USDC'},
     137:{'0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':'USDC','0x2791bca1f2de4661ed88a30c99a7a9449aa84174':'USDC.e','0xc2132d05d31c914a87c6611c10748aeb04b58e8f':'USDT0'},
     42161:{'0xaf88d065e77c8cc2239327c5edb3a432268e5831':'USDC','0xff970a61a04b1ca14834a43f5de4533ebddb5cc8':'USDC.e','0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9':'USDT'}}
def d(ts): return dt.datetime.fromtimestamp(int(ts),dt.UTC).strftime('%Y-%m-%d')
res={}
for ch in (1,137,42161):
    tt=json.load(open(f'deep_0x3b6dcfde_{ch}_tokentx.json'))
    I=collections.defaultdict(lambda:{'amt':0,'n':0,'first':9e12,'last':0,'assets':set()}); O=collections.defaultdict(lambda:{'amt':0,'n':0,'first':9e12,'last':0,'assets':set()})
    zero=0
    for x in tt:
        c=x['contractAddress'].lower()
        if c not in OFF[ch]: continue
        v=int(x['value'])/10**int(x['tokenDecimal'])
        if v==0: zero+=1; continue
        f,t=x['from'].lower(),x['to'].lower()
        if t==T: k,D=f,I
        elif f==T: k,D=t,O
        else: continue
        r=D[k]; r['amt']+=v; r['n']+=1; ts=int(x['timeStamp']); r['first']=min(r['first'],ts); r['last']=max(r['last'],ts); r['assets'].add(OFF[ch][c])
    # poison filter: counterparty whose total < 100 $ and sharing 4 first/last hex with a real counterparty (>=100)
    def clean(D):
        real={k for k,r in D.items() if r['amt']>=100}
        allreal={k for k,r in list(I.items())+list(O.items()) if r['amt']>=100}|{T}
        pois=[k for k,r in D.items() if r['amt']<100 and any(k[:6]==a[:6] and k[-4:]==a[-4:] and k!=a for a in allreal)]
        return {k:r for k,r in D.items() if k not in pois}, len(pois), sum(D[k]['amt'] for k in pois)
    Ic,pi,pia=clean(I); Oc,po,poa=clean(O)
    res[ch]=(Ic,Oc)
    print('chain',ch,'in',round(sum(r['amt'] for r in Ic.values())),len(Ic),'| poison in',pi,round(pia,2),'| out',round(sum(r['amt'] for r in Oc.values())),len(Oc),'| poison out',po,round(poa,2),'| zero-value events',zero)
json.dump({ch:[{k:{**r,'assets':sorted(r['assets'])} for k,r in D.items()} for D in res[ch]] for ch in res},open('p4_io_clean.json','w'))
