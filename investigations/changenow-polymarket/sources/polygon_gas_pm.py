#!/usr/bin/env python3
"""POL gas-size recipients of 0x505e7169 (the only real POL gas-fanner, mixed hub, 30d),
crossed with PM activity: direct EOA, or via-proxy (EOA funds a PM-active address)."""
import json, os, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.dirname(os.path.abspath(__file__))
KEY=[l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if l.startswith('ETHERSCAN_API_KEY=')][0]
BASE='https://api.etherscan.io/v2/api'; NOW=time.time(); CUT=NOW-30*86400
UA={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36','Accept':'application/json'}
GASER='0x505e71695e9bc45943c58adec1650577bca68fd9'
STABLES=('0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359',
         '0xc2132d05d31c914a87c6611c10748aeb04b58e8f','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb')

def es(p):
    p=dict(p); p['chainid']=137; p['apikey']=KEY
    for a in range(4):
        try:
            o=json.loads(urllib.request.urlopen(BASE+'?'+urllib.parse.urlencode(p),timeout=35).read())
            if o.get('status')=='1': return o.get('result',[])
            m=str(o.get('result',''))
            if 'No transactions' in m or 'No records' in m: return []
            if 'rate' in m.lower() or 'Max' in m: time.sleep(1+a); continue
            return []
        except Exception: time.sleep(0.5*(a+1))
    return []

def pm_active(w):
    try:
        arr=json.loads(urllib.request.urlopen(urllib.request.Request(
            f'https://data-api.polymarket.com/activity?user={w}&limit=20',headers=UA),timeout=20).read())
        return isinstance(arr,list) and len(arr)>0
    except urllib.error.HTTPError as e:
        return None if e.code!=429 else pm_active(w)
    except Exception: return None

# 1. collect gas-size POL recipients of GASER (30d)
rec={}
page=1
while True:
    res=es({'module':'account','action':'txlist','address':GASER,'sort':'desc','offset':2000,'page':page})
    if not res: break
    stop=False
    for t in res:
        if int(t['timeStamp'])<CUT: stop=True; break
        if t.get('from','').lower()==GASER and t.get('isError','0')=='0':
            pol=int(t['value'])/1e18
            if 0.005<=pol<=5:
                w=t['to'].lower(); ts=int(t['timeStamp'])
                if w not in rec: rec[w]={'wallet':w,'gas_pol':round(pol,6),'nb':1,'tx':t['hash'],'ts':ts}
                else:
                    rec[w]['nb']+=1
                    if ts>rec[w]['ts']: rec[w].update(gas_pol=round(pol,6),tx=t['hash'],ts=ts)
    if stop or len(res)<2000: break
    page+=1
    if page>20: break
wallets=list(rec.values())
print(f'gas-size POL recipients of {GASER[:12]} (30d): {len(wallets)}')

# 2. PM cross: direct + via-proxy(1-hop)
def classify(d):
    w=d['wallet']
    if pm_active(w): return {**d,'pm_link':'direct','pm_proxy':w}
    # via-proxy: EOA outbound stables -> any recipient PM-active?
    outs=set()
    for tok in STABLES:
        for t in es({'module':'account','action':'tokentx','address':w,'contractaddress':tok,'sort':'desc','offset':50,'page':1}):
            if isinstance(t,dict) and t.get('from','').lower()==w:
                outs.add(t.get('to','').lower())
    for x in list(outs)[:8]:
        if pm_active(x): return {**d,'pm_link':'via_proxy','pm_proxy':x}
    return {**d,'pm_link':'non','pm_proxy':''}

results=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    for i,r in enumerate(ex.map(classify, wallets)):
        results.append(r)
        if i%50==0: print(f'  {i}/{len(wallets)}')

results.sort(key=lambda r:-r['ts'])
import csv
CSV=os.path.join(OUT,'state','polygon_gas_pm.csv')
with open(CSV,'w',newline='') as f:
    wr=csv.writer(f); wr.writerow(['wallet','gas_pol','nb_gas','recent_tx','timestamp','datetime_utc','pm_link','pm_proxy'])
    for r in results:
        wr.writerow([r['wallet'],r['gas_pol'],r['nb'],r['tx'],r['ts'],time.strftime('%Y-%m-%d %H:%M',time.gmtime(r['ts'])),r['pm_link'],r['pm_proxy']])
from collections import Counter
c=Counter(r['pm_link'] for r in results)
print('\\n=== RESULT ===')
print(f'gaser (mixed hub, NOT pure CN gaser): {GASER}')
print(f'POL gas-size recipients (30d): {len(results)}')
print(f'PM-link: {dict(c)}')
print(f'CSV -> {CSV}')
print('\\n--- PM-linked wallets (direct/via_proxy) ---')
for r in results:
    if r['pm_link']!='non':
        print("  %s  gas=%s x%s  %s  proxy=%s" % (r['wallet'], r['gas_pol'], r['nb'], r['pm_link'], r['pm_proxy']))
