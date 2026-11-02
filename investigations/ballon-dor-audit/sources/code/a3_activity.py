"""Audit: wallet histories re-read from the public Data API, and withdrawal timing against unnamed wallets. Public reads only, nothing written outside this audit folder."""
import glob,gzip,json,os,statistics,sys,time
from collections import Counter,defaultdict
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
calls=0
def history(w):
    global calls
    rows,cursor=[],None
    for _ in range(40):
        p=dict(user=w,limit=500,sort_by='TIMESTAMP',sort_direction='ASC',exclude_deposits_withdrawals='false')
        if cursor:p['cursor']=cursor
        for attempt in range(5):
            r=http.get('https://data-api.polymarket.com/v2/activity',params=p);calls+=1
            if r.status_code==200:break
            time.sleep(3*(attempt+1))
        r.raise_for_status();b=r.json();rows+=b.get('data',[]);cursor=(b.get('pagination') or {}).get('next_cursor');time.sleep(.5)
        if not cursor:return rows,True
    return rows,False
RES=1793059200
summary={}
print('=== re-read of the 11 histories against the case files')
acts={}
for s,c in cases.items():
    rows,complete=history(c['address']);acts[s]=rows
    by=Counter();cash=defaultdict(float)
    for r in rows:
        k=r['type']+('_'+r.get('side','') if r['type']=='TRADE' else '');by[k]+=1;cash[k]+=float(r.get('usdc_size') or 0)
    dep={r['transaction_hash'].lower():float(r['usdc_size']) for r in rows if r['type']=='DEPOSIT'}
    wd={r['transaction_hash'].lower():float(r['usdc_size']) for r in rows if r['type']=='WITHDRAWAL'}
    d0={d['tx'].lower():d['usd'] for d in c['deposits']};w0={d['tx'].lower():d['usd'] for d in c['withdrawals']}
    same=all(abs(dep.get(k,-1)-v)<.001 for k,v in d0.items()) and set(dep)==set(d0) and all(abs(wd.get(k,-1)-v)<.001 for k,v in w0.items()) and set(wd)==set(w0)
    ref=cash.get('REFERRAL_REWARD',0)
    print(s,'rows',len(rows),'was',c['rows'],'complete',complete,'same deposits+withdrawals',same,'referral',round(ref,4),'types',{k:v for k,v in by.items() if k not in('TRADE_BUY','TRADE_SELL')})
print('calls',calls)
json.dump({s:[{k:r.get(k) for k in('timestamp','type','side','usdc_size','title','outcome','asset')} for r in v] for s,v in acts.items()},gzip.open(OUT+'a3_named_activity.json.gz','wt'))
print('\n=== what preceded each main withdrawal')
for s,c in cases.items():
    big=max(c['withdrawals'],key=lambda w:w['usd'])
    prior=[r for r in acts[s] if r['timestamp']<=big['at'] and r['type'] in('REDEEM','TRADE')and float(r.get('usdc_size') or 0)>=1]
    last=prior[-1]
    red=[r for r in acts[s] if r['type']=='REDEEM']
    cash_in_last_hour=sum(float(r['usdc_size'] or 0) for r in acts[s] if big['at']-3600<=r['timestamp']<=big['at'] and (r['type']=='REDEEM' or (r['type']=='TRADE' and r['side']=='SELL')))
    summary[s]=dict(at=big['at'],delay_min=round((big['at']-last['timestamp'])/60,1),last=last['type'],last_title=(last.get('title') or '')[:40])
    print(time.strftime('%m-%d %H:%M:%S',time.gmtime(big['at'])),s,round(big['usd']),'delay since last sale/redemption',summary[s]['delay_min'],'min',last['type'],(last.get('title') or '')[:46],'| cash in 1h',round(cash_in_last_hour),'| first redeem',time.strftime('%m-%d %H:%M',time.gmtime(red[0]['timestamp'])) if red else None)
print('\n=== unnamed wallets, same reader')
det=[json.loads(l) for l in open(I+'controls/funding_baseline_detail.jsonl')]
comp=[r for r in det if r['group']!='named']
rows_out=[]
for r in comp:
    try:
        h,complete=history(r['wallet'])
    except Exception as e:
        print('ERR',r['wallet'][:10],str(e)[:60]);continue
    wds=[x for x in h if x['type']=='WITHDRAWAL' and x['timestamp']>=RES-3*3600]
    if wds:
        b=max(wds,key=lambda x:float(x['usdc_size']));rows_out.append(dict(group=r['group'],wallet=r['wallet'],at=b['timestamp'],usd=float(b['usdc_size']),n=len(wds)))
    else: rows_out.append(dict(group=r['group'],wallet=r['wallet'],at=None,usd=0,n=0))
json.dump(rows_out,open(OUT+'a3_comparator_withdrawals.json','w'),indent=0)
print('calls',calls,'with a large withdrawal after the ceremony',Counter((x['group'],bool(x['at'])) for x in rows_out))
for x in sorted((y for y in rows_out if y['at']),key=lambda y:y['at']):print(time.strftime('%m-%d %H:%M:%S',time.gmtime(x['at'])),x['group'],x['wallet'][:10],round(x['usd']))
