"""Phase 8 : séries CLOB (pas 1 min) autour des événements échantillonnés : [T-65 min, T+6 h 05].
Fenêtres fusionnées par jeton en tranches de <= 6,5 jours. Résultat : p8/prices/{asset}.json = liste [t,p] triée."""
import json,os,sys
import pandas as pd
from common2 import http
S=pd.read_pickle('p8/sample_events.pkl')
K,N=(int(sys.argv[1]),int(sys.argv[2])) if len(sys.argv)>2 else (0,1)
PRE,POST,MAXSPAN=3900,21900,int(6.5*86400)
for j,(asset,g) in enumerate(S.groupby('asset')):
    if j%N!=K: continue
    fp=f'p8/prices/{asset}.json'
    if os.path.exists(fp): continue
    ts=sorted(g.ts.unique()); chunks=[]; s=ts[0]-PRE; e=ts[0]+POST
    for t in ts[1:]:
        if t+POST-s<=MAXSPAN: e=max(e,t+POST)
        else: chunks.append((s,e)); s=t-PRE; e=t+POST
    chunks.append((s,e))
    pts={}
    for s,e in chunks:
        try:
            d=http(f'https://clob.polymarket.com/prices-history?market={asset}&startTs={int(s)}&endTs={int(e)}&fidelity=1',cache=False)
            for p in (d.get('history',[]) if isinstance(d,dict) else []): pts[p['t']]=p['p']
        except Exception as ex: pass
    json.dump(sorted(pts.items()),open(fp,'w'))
print('done',K)
