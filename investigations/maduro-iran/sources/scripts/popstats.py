import json,sys,statistics as st,datetime as dt
from collections import defaultdict
EX='0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e'
def role_info(ev,t0,t1):
    R=defaultdict(lambda: dict(taker_cap=0.0,maker_cap=0.0,first_taker=None,first_maker=None))
    for l in open(f'fills_{ev}.jsonl'):
        x=json.loads(l)
        if '_range' in x or not (x['mAsset']=='USDC' and x['tAsset']=='Yes' and t0<=x['ts']<t1): continue
        w=x['maker'].lower(); r=R[w]
        if x['taker'].lower()==EX:
            r['taker_cap']+=x['mAmt']; r['first_taker']=min(r['first_taker'] or 1e12,x['ts'])
        else:
            r['maker_cap']+=x['mAmt']; r['first_maker']=min(r['first_maker'] or 1e12,x['ts'])
    return R
def q(v,p):
    v=sorted(v); 
    if not v: return None
    k=(len(v)-1)*p; f=int(k); c=min(f+1,len(v)-1); return v[f]+(v[c]-v[f])*(k-f)
def summ(rows,label):
    if not rows: return dict(group=label,n=0)
    cap=[r['capital'] for r in rows]; vw=[r['vwap'] for r in rows]; dl=[r['delay_to_move_s']/60 for r in rows]
    fl=[r['funding_latency_s']/3600 for r in rows if r.get('funding_latency_s') is not None]
    pn=[r.get('mkt_PnL',0) for r in rows]
    return dict(group=label,n=len(rows),capital_sum=round(sum(cap),2),capital_mean=round(st.mean(cap),2),capital_median=round(st.median(cap),2),
        top1_share=round(max(cap)/sum(cap),3), winrate_mkt=round(sum(1 for p in pn if p>0)/len(pn),3), mkt_PnL_sum=round(sum(pn),2), mkt_PnL_median=round(st.median(pn),2),
        vwap_median=round(st.median(vw),4), vwap_q25=round(q(vw,.25),4), vwap_q75=round(q(vw,.75),4),
        delay_min_median=round(st.median(dl),1), delay_q25=round(q(dl,.25),1), delay_q75=round(q(dl,.75),1),
        fundlat_h_median=round(st.median(fl),2) if fl else None, share_funded_lt1h=round(sum(1 for x in fl if x<1)/len(rows),3), n_with_funding_obs=len(fl),
        taker_share_capital=round(sum(r['taker_cap'] for r in rows)/max(1e-9,sum(cap)),3))
def run(ev,t0,t1):
    P=json.load(open(f'pop_{ev}.json')); R=role_info(ev,t0,t1)
    for r in P: r.update(R[r['wallet']])
    net=[r for r in P if r.get('network')]; jul=[r for r in P if r.get('july')]
    linked=[r for r in P if not r.get('network') and not r.get('july') and r.get('graph_links')]
    indep=[r for r in P if not r.get('network') and not r.get('july') and not r.get('graph_links')]
    fid=[r for r in P if r.get('funding_identifiable')]; nof=[r for r in P if not r.get('funding_identifiable')]
    out=[summ(P,'ALL'),summ(net,'réseau identifié'),summ(jul,'comptes juillet (SBet365 etc.)'),summ(linked,'autres liés au graphe'),summ(indep,'indépendants'),summ(fid,'funding identifiable (7j)'),summ(nof,'sans funding identifiable (7j)')]
    # percentile ranks of network wallets
    ranks=[]
    for r in net+jul:
        def pr(key,rev=False):
            v=[x[key] for x in P if x.get(key) is not None]; 
            return round(sum(1 for x in v if (x<r[key] if not rev else x>r[key]))/len(v),3)
        ranks.append(dict(wallet=r['wallet'],name=r.get('network') or r.get('july'),first_buy=r['first_buy'],capital=r['capital'],vwap=r['vwap'],delay_min=round(r['delay_to_move_s']/60,1),
            fundlat_h=round(r['funding_latency_s']/3600,3) if r.get('funding_latency_s') is not None else None,
            pct_capital=pr('capital'),pct_earlier=pr('delay_to_move_s'),pct_cheaper=pr('vwap',rev=True),taker_cap=round(r['taker_cap'],2),maker_cap=round(r['maker_cap'],2)))
    return P,out,ranks
if __name__=='__main__':
    W={'maduro':(1767416400,1767420720),'iran':(1772256480,1772259180),'maduroX':(1767333600,1767416400),'iranA':(1772139600,1772148600),'iranB':(1772202600,1772214300)}
    for ev in sys.argv[1:]:
        t0,t1=W.get(ev,(0,9e12))
        P,out,ranks=run(ev,t0,t1)
        print('=====',ev)
        for o in out: print(json.dumps(o,ensure_ascii=False))
        print('RANKS (pct = share of population strictly below/earlier/cheaper):')
        for r in ranks: print(json.dumps(r,ensure_ascii=False))
        json.dump(dict(pop=P,groups=out,ranks=ranks),open(f'popstats_{ev}.json','w'),indent=1)
