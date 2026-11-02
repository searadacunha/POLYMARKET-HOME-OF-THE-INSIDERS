import sys, json, datetime as dt
sys.path.insert(0,'.')
from common import *
def ts(t): return dt.datetime.utcfromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M:%S')
STABLE={'0x2791bca1f2de4661ed88a30c99a7a9449aa84174':'USDC.e','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':'USDC','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb':'pUSD'}
def run(w):
    w=w.lower()
    act=pm_activity(w)
    comp={}
    for a in act:
        t=a['type']; k=t if t!='TRADE' else 'TRADE_'+a.get('side','?')
        comp.setdefault(k,[0,0.0]); comp[k][0]+=1; comp[k][1]+=float(a.get('usdcSize') or 0)
    val=http(f'https://data-api.polymarket.com/value?user={w}',cache=False)
    pos=http(f'https://data-api.polymarket.com/positions?user={w}&sizeThreshold=0&limit=500',cache=False)
    tt=es_all(137,'tokentx',w)
    flows=[]
    for x in tt:
        c=x['contractAddress'].lower()
        sym=STABLE.get(c, x['tokenSymbol'])
        amt=int(x['value'])/10**int(x['tokenDecimal'] or 0)
        d='IN' if x['to'].lower()==w else 'OUT'
        cp=x['from'] if d=='IN' else x['to']
        flows.append(dict(ts=int(x['timeStamp']),t=ts(x['timeStamp']),dir=d,sym=sym,token=c,amt=amt,cp=cp.lower(),hash=x['hash']))
    return dict(wallet=w,activity=act,comp=comp,value=val,positions=pos,flows=flows)
if __name__=='__main__':
    for w in sys.argv[1:]:
        r=run(w)
        json.dump(r,open(f'out_{w[:10]}.json','w'))
        print('=====',w,'activity rows',len(r['activity']))
        for k,v in sorted(r['comp'].items()): print(f'  {k:12s} n={v[0]:5d} usdc={v[1]:,.2f}')
        print('  value',r['value'],' open positions',len(r['positions']))
        from collections import defaultdict
        agg=defaultdict(lambda:[0,0.0])
        for f in r['flows']:
            if f['sym'] in ('USDC.e','USDC','pUSD'):
                k=(f['dir'],f['sym'],f['cp']); agg[k][0]+=1; agg[k][1]+=f['amt']
        for k,v in sorted(agg.items(), key=lambda kv:-kv[1][1]):
            if v[1]>=1: print(f'  {k[0]:3s} {k[1]:6s} {k[2]} n={v[0]} ${v[1]:,.2f}')
