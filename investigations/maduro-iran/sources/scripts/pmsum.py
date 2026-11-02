import json,glob,sys,datetime as dt
from collections import defaultdict
def T(t): return dt.datetime.fromtimestamp(int(t),dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
def run(w,keys=('Maduro','Iran','Venezuela','Khamenei'),top=12):
    r=json.load(open(glob.glob(f'out_{w[:10].lower()}*.json')[0]))
    act=r['activity']
    m=defaultdict(lambda: defaultdict(float)); tot=defaultdict(float)
    for a in act:
        k=a['type'] if a['type']!='TRADE' else a['side']
        m[a.get('title','?')][k]+=float(a.get('usdcSize') or 0); tot[k]+=float(a.get('usdcSize') or 0)
    cur=sum(float(x.get('currentValue') or 0) for x in r['positions'])
    pnl=tot['SELL']+tot['REDEEM']+tot['MERGE']+cur-tot['BUY']-tot['SPLIT']
    print(f"===== {r['wallet']} name={act[0].get('name') if act else None} rows={len(act)} first={T(min(int(a['timestamp']) for a in act)) if act else None} last={T(max(int(a['timestamp']) for a in act)) if act else None} markets={len(m)}")
    print(f"  COMPONENTS BUY={tot['BUY']:,.2f} SPLIT={tot['SPLIT']:,.2f} SELL={tot['SELL']:,.2f} REDEEM={tot['REDEEM']:,.2f} MERGE={tot['MERGE']:,.2f} CUR={cur:,.2f} => PnL={pnl:,.2f}")
    for t,v in sorted(m.items(), key=lambda kv:-sum(kv[1].values()))[:top]:
        print(f"  {t[:60]:60s} "+' '.join(f"{k}={v[k]:,.2f}" for k in ('BUY','SELL','SPLIT','MERGE','REDEEM') if v.get(k)))
    for a in sorted(act,key=lambda a:int(a['timestamp'])):
        if any(k in a.get('title','') for k in keys) and a['type'] in ('TRADE','REDEEM','SPLIT','MERGE'):
            print('   ',T(a['timestamp']), a['type'], a.get('side',''), a.get('outcome',''), f"px={float(a.get('price') or 0):.4f}", f"${float(a.get('usdcSize') or 0):,.2f}", a.get('title','')[:48], a.get('transactionHash','')[:12])
    return dict(wallet=r['wallet'],name=act[0].get('name') if act else None,pnl=pnl,**{k:tot[k] for k in ('BUY','SPLIT','SELL','REDEEM','MERGE')},cur=cur)
if __name__=='__main__':
    for w in sys.argv[1:]: run(w)
