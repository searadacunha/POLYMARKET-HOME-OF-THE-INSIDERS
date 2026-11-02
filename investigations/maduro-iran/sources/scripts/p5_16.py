import json,csv,datetime as dt,bisect,collections,statistics as st
T='0x3b6dcfde35e53fb7dca8571f23286631b5123c5b'
OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'USDC','0xdac17f958d2ee523a2206206994597c13d831ec7':'USDT'}
W={'0x4a9a1675':'0x4a9a16755a6bf64291cd2c9eb027b39c129ff58d','0xb7152d59':'0xb7152d5900da932b7fc3cac97aebfc815f88d5ca','0xb93e3d70':'0xb93e3d70ac9cacd51764f09ae0d01b905dc291e1','0x26c50e67':'0x26c50e673fca05131c9b9f23d213b977d9a34c77'}
rows=list(csv.DictReader(open('/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase4/16_paiements_service.csv')))
D={};HD={};BYD={}
for k,a in W.items():
    tt=json.load(open(f'deep_{a[:10]}_1_tokentx.json')); tx={x['hash']:x for x in json.load(open(f'deep_{a[:10]}_1_txlist.json')) if x['from'].lower()==a}
    pay=sorted((int(x['timeStamp']),x['to'].lower(),int(x['value'])/1e6,x['hash']) for x in tt if x['from'].lower()==a and x['contractAddress'].lower() in OFF and int(x['value'])>=10**6)
    ref=sorted((int(x['timeStamp']),int(x['value'])/1e6,x['hash']) for x in tt if x['to'].lower()==a and x['from'].lower()==T and x['contractAddress'].lower() in OFF)
    amts=sorted(p[2] for p in pay)
    gp=sorted(int(x['gasPrice']) for x in tx.values())
    D[k]=(pay,ref,amts,tx,gp)
    HD[k]={p[3]:p[1] for p in pay}; BYD[k]=collections.defaultdict(list)
    for p in pay: BYD[k][p[1]].append(p[0])
out=[]
for r in rows:
    k=r['service_wallet']
    if k not in D: out.append({**r}); continue
    pay,ref,amts,tx,gp=D[k]
    h=r['hash']; ts=int(dt.datetime.strptime(r['date'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=dt.UTC).timestamp())
    i=bisect.bisect_right([x[0] for x in ref],ts)-1
    lr=ref[i] if i>=0 else None
    t=tx.get(h,{})
    dest=HD[k].get(h); prev=[p for p in BYD[k].get(dest,[]) if p<ts]
    tl=[p[0] for p in pay]; win=bisect.bisect_right(tl,ts+600)-bisect.bisect_left(tl,ts-600)
    amt=float(r['amount']); pr=bisect.bisect_left(amts,amt)/len(amts)
    gpr=bisect.bisect_left(gp,int(t.get('gasPrice',0)))/len(gp) if t else None
    o={'n':r['n'],'date':r['date'],'payer':k,'amount':amt,'token':r['token'],'dest':r['destination'],'pm':r['pm_account'],
       'last_refill_utc':dt.datetime.fromtimestamp(lr[0],dt.UTC).strftime('%Y-%m-%d %H:%M') if lr else '','last_refill_amt':lr[1] if lr else '','min_since_refill':round((ts-lr[0])/60,1) if lr else '',
       'payer_payouts_pm10min':win,'amount_percentile_payer':round(pr,3),'prior_payouts_same_dest_same_payer':len(prev),
       'gasLimit':t.get('gas'),'gasPrice_gwei':round(int(t['gasPrice'])/1e9,3) if t else '','gasPrice_pct':round(gpr,3) if gpr is not None else '','nonce':t.get('nonce'),'fn':(t.get('functionName') or '')[:20],
       'hour_utc':r['date'][11:13]}
    out.append(o)
    print(o['n'],o['date'],k,amt,o['token'],'| refill',o['last_refill_utc'],o['last_refill_amt'],o['min_since_refill'],'min | ±10min',win,'| pct',o['amount_percentile_payer'],'| prior same dest',len(prev),'| gas',o['gasLimit'],o['gasPrice_gwei'],o['gasPrice_pct'],'|',o['fn'])
json.dump(out,open('p5_16.json','w'))
