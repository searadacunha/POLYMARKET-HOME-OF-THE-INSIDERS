"""Phase 8 : features observables à T (uniquement le passé) + drapeaux de signaux sur listes de trades.
Aucune donnée postérieure à T n'est utilisée ici."""
import json,glob,bisect,collections,datetime as dt
import pandas as pd, numpy as np
U={m['conditionId']:m for m in json.load(open('p8/universe.json'))}
A={'0x168b100d7a6620a2f49a455344c2c006eaf1714b':'Chiwawas','0x5621116629c5d640c8186f577362478cc6605245':'TacticalInsiderNews','0x38745db27f7360a287f6ca3c9b6a6a9c76149801':'Planktonbets','0x60280beffdfeaf962de4e6397ab49ed05a1b99e1':'X34','0x834079f62fa9b4b0bdfad5b8b7a841e8267da024':'chileno777','0xbf32f7a77ccea8bba647fea63d438ce1778b1762':'154x838hjd6','0x56efadc9defe5b7a21af751e0d026f2cf54136db':'Neodbs','0xe9b80c387ba77a585423b13c850c2e126c3befd8':'Mrs.Joker'}
rows=[]
for cid,m in U.items():
    fp=f'p8/trades/{cid}.json'
    try: d=json.load(open(fp))
    except Exception: continue
    end=int(dt.datetime.fromisoformat(m['endDate'].replace('Z','+00:00')).timestamp()) if m.get('endDate') else None
    try:
        op=[float(x) for x in json.loads(m['outcomePrices'])]
    except Exception: op=None
    for r in d['rows']:
        try: px=float(r['price']); sz=float(r['size'])
        except Exception: continue
        oi=r.get('outcomeIndex')
        win=None
        if op is not None and oi is not None and oi<len(op):
            win=1 if op[oi]>=0.99 else (0 if op[oi]<=0.01 else None)
        rows.append((cid,m['split'],m.get('cat'),r['proxyWallet'].lower(),r['side'],r['asset'],px,sz,px*sz,int(r['timestamp']),oi,win,end,d.get('maybe_truncated',False),r.get('transactionHash')))
df=pd.DataFrame(rows,columns=['cid','split','cat','wallet','side','asset','price','size','usd','ts','oi','win','end','trunc','tx'])
df=df.sort_values(['ts']).reset_index(drop=True)
print('rows',len(df),'markets',df.cid.nunique(),'wallets',df.wallet.nunique())
# prior trades in universe (global chronological)
df['prior_trades_univ']=df.groupby('wallet').cumcount()
# per-market features
out=[]
for cid,g in df.groupby('cid',sort=False):
    g=g.sort_values('ts'); past=[]; seen=set(); rank=[]; first=[]
    thr90=[]
    for u,w in zip(g.usd.values,g.wallet.values):
        n=len(past)
        rank.append(bisect.bisect_left(past,u)/n if n>=30 else np.nan)
        first.append(w not in seen)
        bisect.insort(past,u); seen.add(w)
    g=g.assign(size_rank_mkt=rank,first_in_mkt=first)
    out.append(g)
df=pd.concat(out).sort_values('ts').reset_index(drop=True)
# conv_30m and accum per token
conv=np.zeros(len(df),dtype=int); accum=np.zeros(len(df),dtype=bool)
for asset,g in df.groupby('asset',sort=False):
    idx=g.index.values; ts=g.ts.values; w=g.wallet.values; sd=g.side.values; rk=g.size_rank_mkt.values
    buys=collections.deque()  # (ts,wallet) of large buys
    hist=collections.defaultdict(collections.deque)  # wallet -> deque of (ts,side)
    for i,j in enumerate(idx):
        t=ts[i]
        while buys and buys[0][0]<t-1800: buys.popleft()
        if sd[i]=='BUY':
            conv[j]=len({x[1] for x in buys if x[1]!=w[i]})
        h=hist[w[i]]
        while h and h[0][0]<t-86400: h.popleft()
        if sd[i]=='BUY':
            accum[j]=sum(1 for x in h if x[1]=='BUY')>=3 and not any(x[1]=='SELL' for x in h)
        h.append((t,sd[i]))
        if sd[i]=='BUY' and not np.isnan(rk[i]) and rk[i]>=0.90: buys.append((t,w[i]))
df['conv_30m']=conv; df['accum']=accum
df['hours_to_end']=(df.end-df.ts)/3600
df['popA']=df.wallet.map(A)
ev=df[df.side=='BUY'].copy()
ev['S_LARGE']=(ev.size_rank_mkt>=0.99)&(ev.usd>=5000)
ev['S_LONGSHOT_LARGE']=(ev.price<=0.20)&(ev.size_rank_mkt>=0.95)
ev['S_CONV']=(ev.conv_30m>=2)&(ev.size_rank_mkt>=0.90)
ev['S_ACCUM']=ev.accum
ev['S_FIRST_LARGE']=ev.first_in_mkt&(ev.prior_trades_univ<=2)&(ev.size_rank_mkt>=0.95)
ev['eid']=ev.index
ev.to_pickle('p8/events.pkl'); df.to_pickle('p8/alltrades.pkl')
print('BUY events',len(ev)); print(ev.groupby('split')[['S_LARGE','S_LONGSHOT_LARGE','S_CONV','S_ACCUM','S_FIRST_LARGE']].sum())
print('popA events',ev.popA.notna().sum(), ev[ev.popA.notna()].groupby('popA').size().to_dict())
