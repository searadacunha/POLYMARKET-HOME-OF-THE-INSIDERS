import json,collections,statistics as st,datetime as dt,math,bisect
OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7'}
W={'MP6':'0xd42f958e1c3e2a10e5d66343c4c9a57726e5b4b6','MP8':'0x22f6cc8738308a8c92a6a71ea67832463d1fec0d','b93e':'0xb93e3d70ac9cacd51764f09ae0d01b905dc291e1','26c5':'0x26c50e673fca05131c9b9f23d213b977d9a34c77','4a9a':'0x4a9a16755a6bf64291cd2c9eb027b39c129ff58d','b715':'0xb7152d5900da932b7fc3cac97aebfc815f88d5ca'}
def d(t): return dt.datetime.fromtimestamp(t,dt.UTC)
GO=int(dt.datetime(2024,5,21,tzinfo=dt.UTC).timestamp())
# fenêtres comparables de 12 mois : MP avant GO, G1 après GO, G2 depuis démarrage
WIN={'MP6':(GO-365*86400,GO),'MP8':(GO-365*86400,GO),'b93e':(GO,GO+365*86400),'26c5':(GO,GO+365*86400),'4a9a':(0,9e12),'b715':(0,9e12)}
out={}
for k,a in W.items():
    tx=[x for x in json.load(open(f'deep_{a[:10]}_1_txlist.json'))]
    tt=json.load(open(f'deep_{a[:10]}_1_tokentx.json'))
    sent={x['hash']:x for x in tx if x['from'].lower()==a}
    lo,hi=WIN[k]
    pay=sorted([(int(x['timeStamp']),int(x['blockNumber']),x['hash'],int(x['value'])/1e6,x['to'].lower()) for x in tt if x['from'].lower()==a and x['contractAddress'].lower() in OFF and int(x['value'])>=10**6 and lo<=int(x['timeStamp'])<hi])
    # funding events (all inbound stable + ETH), any sender
    fund=sorted([(int(x['timeStamp']),x['from'].lower(),int(x['value'])/1e6) for x in tt if x['to'].lower()==a and x['contractAddress'].lower() in OFF and int(x['value'])>=10**9 and lo<=int(x['timeStamp'])<hi])
    s=[sent[p[2]] for p in pay if p[2] in sent]
    gl=collections.Counter(x['gas'] for x in s)
    gp=[int(x['gasPrice'])/1e9 for x in s]
    nonces=sorted(int(x['nonce']) for x in sent.values())
    gaps_n=sum(1 for i in range(1,len(nonces)) if nonces[i]!=nonces[i-1]+1)
    fails=sum(1 for x in sent.values() if x.get('isError')=='1')
    ts=[p[0] for p in pay]; iv=[ts[i]-ts[i-1] for i in range(1,len(ts))]
    blk=collections.Counter(p[1] for p in pay); batch=collections.Counter(blk.values())
    h=collections.Counter(d(t).hour for t in ts); w=collections.Counter(d(t).weekday() for t in ts)
    # delay from funding to next payout, payouts in the 30 min after funding vs baseline
    fts=[f[0] for f in fund]
    after=[]
    for f in fts:
        i=bisect.bisect_left(ts,f)
        if i<len(ts): after.append(ts[i]-f)
    fsz=collections.Counter(round(f[2]) for f in fund)
    fsrc=collections.Counter(f[1] for f in fund)
    days=max(1,(ts[-1]-ts[0])/86400) if ts else 1
    out[k]=dict(window=(str(d(lo).date()) if lo else 'début',str(d(min(hi,ts[-1] if ts else hi)).date())),payouts=len(pay),per_day=round(len(pay)/days,1),
       gas_limit_top=gl.most_common(3),gasprice_median=round(st.median(gp),3) if gp else None,nonce_gaps=gaps_n,failed_tx=fails,
       interval_median_s=st.median(iv) if iv else None,interval_p10_s=sorted(iv)[len(iv)//10] if iv else None,
       same_block_share=round(sum(c for c in blk.values() if c>1)/len(pay),4) if pay else None,max_batch=max(blk.values()) if pay else None,
       hour_share=[round(h[i]/len(pay),4) for i in range(24)],weekend_share=round((w[5]+w[6])/len(pay),4) if pay else None,
       median_amount=st.median([p[3] for p in pay]) if pay else None,integer_share=round(sum(1 for p in pay if abs(p[3]-round(p[3]))<1e-9)/len(pay),4) if pay else None,
       fundings=len(fund),funding_sizes=fsz.most_common(4),funding_sources=[(s[:10],n) for s,n in fsrc.most_common(4)],delay_funding_to_next_payout_median_s=st.median(after) if after else None)
for k,v in out.items(): print(k,{kk:vv for kk,vv in v.items() if kk!='hour_share'})
def corr(a,b):
    xa=out[a]['hour_share'];xb=out[b]['hour_share'];ma,mb=sum(xa)/24,sum(xb)/24
    return round(sum((p-ma)*(q-mb) for p,q in zip(xa,xb))/math.sqrt(sum((p-ma)**2 for p in xa)*sum((q-mb)**2 for q in xb)),3)
print('hour corr',{f'{a}/{b}':corr(a,b) for a,b in [('MP6','MP8'),('MP6','b93e'),('MP8','26c5'),('b93e','4a9a'),('MP6','4a9a')]})
json.dump(out,open('p6_operator.json','w'),default=str)
