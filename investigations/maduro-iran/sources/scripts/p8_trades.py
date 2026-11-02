"""Collecte des trades preneurs >= 100 $ (data-api) pour chaque marché de l'univers. Reprise possible."""
import json,os,sys
from common2 import http
U=json.load(open('p8/universe.json'))
K,N=(int(sys.argv[1]),int(sys.argv[2])) if len(sys.argv)>2 else (0,1)
U=[m for i,m in enumerate(U) if i%N==K]
done=0; trunc=0
for i,m in enumerate(U):
    fp=f"p8/trades/{m['conditionId']}.json"
    if os.path.exists(fp): done+=1; continue
    rows=[]; off=0; t=False
    while True:
        try: d=http(f"https://data-api.polymarket.com/trades?market={m['conditionId']}&limit=500&offset={off}&filterType=CASH&filterAmount=100",cache=False)
        except Exception as e: d=None
        if not isinstance(d,list) or not d: 
            if off>=3000 and d==[] : t=True
            break
        rows+=[{k:x.get(k) for k in ('proxyWallet','side','asset','size','price','timestamp','outcome','outcomeIndex','transactionHash')} for x in d]
        if len(d)<500: break
        off+=500
        if off>10000: t=True; break
    json.dump({'rows':rows,'maybe_truncated':t or (len(rows)>=3000 and len(rows)%500==0)},open(fp,'w'))
    done+=1
    if done%100==0: print(done,'markets',flush=True)
print('finished',done)
