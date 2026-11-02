"""Exploratory. Daily price and flow of the key outcomes, and the part of the named wallets. Prices are traded prices: no dated book exists."""
import gzip,json,re,sys,time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,'collective/code');sys.path.insert(0,'tools')
import rows as R, identities as I
cat=R.catalog()
named={v['address'] for v in I.IDS.values()}
T_END=1793044800
keys={}
for tok,(ev,q,o) in cat.items():
    q=q or ''
    if (ev=='1105364') or (ev=='48361' and o=='Yes' and any(x in q for x in('Harry Kane','Lamine Yamal','Kylian Mbappé'))) or (ev in('1218178','1218179','1225367','1225368') and o=='Yes' and (('Mbappé finish 2nd' in q) or ('Yamal finish 3rd' in q) or ('Rodri finish 4th' in q) or ('Messi finish 5th' in q))) or (ev=='1105369' and o=='Rodri') :
        keys[tok]=q.replace("Will ","").replace(" the 2026 Ballon d'Or?","").replace("Ballon d'Or 2026: ","")[:44]+' | '+o
rows=defaultdict(list)
for r in R.family():
    if r[2] in keys: rows[r[2]].append((r[8],r[3],r[4],r[5],r[6],r[7]))
with gzip.open(R.S/'ballon_2026_20261030/data/trades_minimal.jsonl.gz','rt') as f:
    for l in f:
        r=json.loads(l)
        if r['token_id'] in keys and r['timestamp']>=R.T_FIN and r['timestamp']<T_END:
            rows[r['token_id']].append((r['timestamp'],r['wallet'],r['side'],r['size']*r['price'],r['size'],r['price']))
out={}
for tok,v in rows.items():
    v.sort()
    day=defaultdict(lambda:dict(usd=0.,shares=0.,buy=0.,named=0.,wallets=set(),open=None,close=None,hi=0,lo=9))
    for t,w,s,usd,size,p in v:
        d=day[time.strftime('%m-%d',time.gmtime(t))]
        d['usd']+=usd;d['shares']+=size;d['close']=p;d['open']=d['open'] if d['open'] is not None else p;d['hi']=max(d['hi'],p);d['lo']=min(d['lo'],p)
        if s=='BUY':
            d['buy']+=usd;d['wallets'].add(w)
            if w in named:d['named']+=usd
    out[keys[tok]]={k:dict(vwap=round(x['usd']/x['shares'],3) if x['shares'] else None,open=x['open'],close=x['close'],buy=round(x['buy']),named=round(x['named']),buyers=len(x['wallets'])) for k,x in sorted(day.items())}
Path('collective/exploratoire/price_days.json').write_text(json.dumps(out,ensure_ascii=False,indent=0))
for k,v in out.items():
    print('\n',k)
    for d,x in v.items():
        if d>='10-05' : print('  ',d,'vwap',x['vwap'],'close',round(x['close'],3),'buy$',x['buy'],'named$',x['named'],'buyers',x['buyers'])
