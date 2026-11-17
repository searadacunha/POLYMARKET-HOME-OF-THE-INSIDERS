"""Pre-specified quote diagnostics. Never sends orders; no claimed fill simulation."""
import array, bisect, collections, csv, gzip, itertools, json, math, statistics
from pathlib import Path
from registre import enregistrer
ROOT=Path(__file__).resolve().parents[1]
START=1794614400
SPLITS=[('TRAIN',START,START+86400),('VALIDATION',START+86400,START+172800),('TEST',START+172800,START+219600)]
HORIZONS=[60,300,3600,21600,86400]
COSTS=[('optimistic',0,0),('politics',.04,.001),('stress',.07,.002)]
def before(ts,t,age):
    i=bisect.bisect_right(ts,t)-1
    return i if i>=0 and 0<=t-ts[i]<=age else None
def after(ts,t,wait=5):
    i=bisect.bisect_left(ts,t)
    return i if i<len(ts) and 0<=ts[i]-t<=wait else None
def net(ask,bid,rate,slip):
    entry=ask+rate*ask*(1-ask)+slip
    return bid-rate*bid*(1-bid)-slip-entry,entry
def levels(r,side):
    d=collections.defaultdict(float)
    for x in r[side]:
        p,s=float(x['price']),float(x['size'])
        if not math.isfinite(p) or not math.isfinite(s) or not 0<=p<=1 or s<0: raise ValueError('invalid depth')
        if s: d[p]+=s
    return sorted(d.items(),reverse=(side=='bids'))
def capacity(books,t,side,price):
    if not books: return None
    i=before(books[0],t,2)
    if i is None: return None
    ls=levels(books[1][i],side)
    if not ls or abs(ls[0][0]-price)>1e-8: return None
    return ls[0][1]
def summarize(rows):
    if not rows: return {'n':0,'n_effective_event_families':0,'net_per_share':None,'roi':None,'pnl_10shares':None,'hit_rate':None,'profit_factor':None,'cashflow_drawdown_10shares':None,'ci95_event_bootstrap':None,'depth_supported':0}
    pnl=[r['net'] for r in rows]; pos=sum(max(v,0) for v in pnl); loss=-sum(min(v,0) for v in pnl)
    groups=collections.defaultdict(list)
    for r in rows: groups[r['family']].append(r['net'])
    vals=list(groups.values()); boot=[]
    for ix in itertools.product(range(len(vals)),repeat=len(vals)):
        v=[n for i in ix for n in vals[i]]; boot.append(statistics.mean(v))
    boot.sort(); ci=[boot[int(.025*(len(boot)-1))],boot[math.ceil(.975*(len(boot)-1))]]
    equity=peak=dd=0
    for r in sorted(rows,key=lambda x:x['exit']):
        equity+=10*r['net'];peak=max(peak,equity);dd=max(dd,peak-equity)
    return {'n':len(rows),'n_effective_event_families':len(groups),'net_per_share':statistics.mean(pnl),'roi':sum(pnl)/sum(r['cost'] for r in rows),'pnl_10shares':10*sum(pnl),'hit_rate':sum(v>0 for v in pnl)/len(pnl),'profit_factor':pos/loss if loss else None,'cashflow_drawdown_10shares':dd,'ci95_event_bootstrap':ci,'depth_supported':sum(r['capacity'] is not None and r['capacity']>=10 for r in rows)}
def run():
    quotes={}; conditions={}
    with gzip.open(ROOT/'data/quotes.jsonl.gz','rt') as f:
        for s in f:
            a,t,bid,ask,condition,source_t=json.loads(s)
            if a not in quotes: quotes[a]=tuple(array.array('d') for _ in range(3))
            q=quotes[a]
            if q[0] and t<q[0][-1]: raise ValueError('unordered quotes')
            for ar,v in zip(q,(t,bid,ask)): ar.append(v)
            if condition: conditions[a]=condition
    books={}
    with gzip.open(ROOT/'data/books.jsonl.gz','rt') as f:
        for s in f:
            r=json.loads(s); a=r['asset_id']; pair=books.setdefault(a,([],[]));pair[0].append(r['received']);pair[1].append(r)
    markets=json.loads((ROOT/'data/markets.json').read_text()); yes={m['yes_token']:m for m in markets}
    signals=collections.defaultdict(list)
    for a,m in yes.items():
        if a not in quotes: continue
        ts,bids,asks=quotes[a]
        for t in range(START,START+219600,60):
            i=before(ts,t,5); j=before(ts,t-300,5)
            if i is None or j is None: continue
            mid=(bids[i]+asks[i])/2
            if not .02<=mid<=.98: continue
            mom=mid-(bids[j]+asks[j])/2
            common=(a,float(t),int(mid*10),int(t//3600))
            if mom>=.005: signals['momentum'].append(common)
            if mom<=-.005: signals['reversal'].append(common)
            if abs(mom)<.001: signals['control'].append(common)
            bk=books.get(a); k=before(bk[0],t,5) if bk else None
            if k is not None:
                b=sum(s for p,s in levels(bk[1][k],'bids')[:3]); ask=sum(s for p,s in levels(bk[1][k],'asks')[:3])
                if b+ask>0 and b/(b+ask)>=.8: signals['imbalance'].append(common)
    seen=set(); trade_counts=collections.Counter(); lags=[]
    for line in (ROOT/'data/trades.jsonl').read_text().splitlines():
        r=json.loads(line);trade_counts['all']+=1
        if not all(k in r for k in ('asset_id','price','size','received','t','side','tx')): trade_counts['missing_fields']+=1;continue
        key=tuple(r[k] for k in ('tx','asset_id','side','size','price'))
        if key in seen: trade_counts['duplicate']+=1;continue
        seen.add(key); t=r['received'];a=r['asset_id']
        if not START<=t<START+219600 or a not in yes or r['side']!='BUY' or float(r['price'])*float(r['size'])<1000: continue
        q=quotes.get(a);i=before(q[0],t,5) if q else None
        if i is None: trade_counts['missing_decision_quote']+=1;continue
        mid=(q[1][i]+q[2][i])/2
        if not .02<=mid<=.98:continue
        signals['copy_large'].append((a,t,int(mid*10),int(t//3600)));lags.append(t-r['t'])
    output=[];details=[]
    for split,lo,hi in SPLITS:
      for h in HORIZONS:
       for latency in (1,5,30):
        for cost,rate,slip in COSTS:
         cell={}
         for name in ('control','momentum','reversal','imbalance','copy_large'):
          rows=[]; missing=collections.Counter();n_signal=0
          for a,t,pricebin,hour in signals[name]:
            if not lo<=t<hi:continue
            n_signal+=1;q=quotes[a];i=after(q[0],t+latency)
            if i is None:missing['entry']+=1;continue
            target=q[0][i]+h
            if target>=hi:missing['split_or_censoring']+=1;continue
            j=after(q[0],target)
            if j is None or q[0][j]>=hi:missing['exit']+=1;continue
            value,capital=net(q[2][i],q[1][j],rate,slip)
            ca=capacity(books.get(a),q[0][i],'asks',q[2][i]); cb=capacity(books.get(a),q[0][j],'bids',q[1][j])
            rows.append({'asset':a,'decision':t,'entry':q[0][i],'exit':q[0][j],'ask':q[2][i],'bid':q[1][j],'net':value,'cost':capital,'capacity':min(ca,cb) if ca is not None and cb is not None else None,'family':'nomination' if yes[a]['neg_risk'] else 'xi','match':(a,pricebin,hour)})
          cell[name]=rows
          metrics=summarize(rows); metrics.update(split=split,horizon_s=h,latency_s=latency,cost=cost,signal=name,signals=n_signal,missing=dict(missing))
          metrics['verdict']='DONNEES_INSUFFISANTES' if not rows else 'NON_EXPLOITABLE' if metrics['net_per_share']<=0 else 'PROMETTEUR_NON_VALIDE'
          output.append(metrics)
          if split=='TEST' and h==3600 and latency==5 and cost=='politics':details.extend(dict(r,signal=name) for r in rows)
         controls=collections.defaultdict(list)
         for r in cell['control']:controls[r['match']].append(r['net'])
         for result in output[-5:]:
            diff=[r['net']-statistics.mean(controls[r['match']]) for r in cell[result['signal']] if len(controls[r['match']])>=5]
            result.update(matched_n=len(diff),matched_difference=statistics.mean(diff) if diff else None)
    arb=[]
    for split,lo,hi in SPLITS:
        valid=violations=0;max_edge=None
        for a,m in yes.items():
            other=[b for b,c in conditions.items() if c==m['condition_id'] and b!=a]
            if len(other)!=1:continue
            qa,qb=quotes[a],quotes[other[0]]
            for t in range(lo,hi,60):
                i=before(qa[0],t,2);j=before(qb[0],t,2)
                if i is None or j is None or abs(qa[0][i]-qb[0][j])>2:continue
                valid+=1;edge=1-qa[2][i]-qb[2][j];max_edge=edge if max_edge is None else max(edge,max_edge)
                violations+=edge>1e-9
        arb.append({'split':split,'paired_quotes':valid,'gross_violations':violations,'max_gross_edge_per_pair':max_edge})
    summary={'cells':output,'arbitrage':arb,'copy_trade_counts':dict(trade_counts),'copy_lag_median_s':statistics.median(lags) if lags else None,'copy_signals':len(lags),'comparisons':679,'bonferroni_alpha':.05/679,'limitations':['Quote diagnostics only; unknown fills, fees and gaps','Two event families; bootstrap intervals unreliable','24h horizon censored by daily splits']}
    (ROOT/'derived/results.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'derived/test_1h_5s_trades.json').write_text(json.dumps(details,indent=2))
    with (ROOT/'derived/results.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(output[0]));w.writeheader();w.writerows(output)
    enregistrer(str(ROOT),test='D_B_quote_diagnostics_and_E_pair_gate',declare=True,n=sum(x['n'] for x in output),n_effectif=2,agent='Codex',n_comparaisons=678,sortie='derived/results.json',note='Exploratory overlapping cells; two independent event families; no validated fills')
    print(json.dumps({'cells':len(output),'arbitrage':arb,'copy_signals':len(lags),'copy_lag_median_s':summary['copy_lag_median_s']},indent=2))
def selftest():
    assert before([1.,2.,4.],3.,1)==1 and before([1.],4.,2) is None
    assert after([1.,2.,4.],3.,1)==2 and after([1.],2.) is None
    assert net(.51,.49,0,0)[0]<0 and net(.51,.49,.04,.001)[0]<net(.51,.49,0,0)[0]
    assert net(.51,.60,.04,.001)[0]>0
    b=([1.],[{'asks':[{'price':'.5','size':'4'}],'bids':[{'price':'.4','size':'3'}]}])
    assert capacity(b,1,'asks',.5)==4 and capacity(b,4,'asks',.5) is None and capacity(b,1,'asks',.6) is None
    assert summarize([])['roi'] is None
    for move in (0,.002,.1):
        rows=[{'net':net(.5,.49+move,.04,.001)[0],'cost':.511,'family':str(i%2),'exit':i,'capacity':10} for i in range(20)]
        s=summarize(rows); assert (s['net_per_share']>0)==(move==.1)
    print('PASS: causal lookup, missing data, fees on losses, spread, depth, null/moderate/strong economics')
if __name__=='__main__':
    import sys
    selftest() if '--selftest' in sys.argv else run()
