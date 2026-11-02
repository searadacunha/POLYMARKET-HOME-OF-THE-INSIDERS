import sys,json,datetime as dt; sys.path.insert(0,'.')
from common import *
from collections import Counter
H={'User-Agent':'curl/8.4.0'}
def trc20(a,maxpages=10,**kw):
    rows=[]; fp=None
    extra=''.join(f'&{k}={v}' for k,v in kw.items())
    for i in range(maxpages):
        url=f'https://api.trongrid.io/v1/accounts/{a}/transactions/trc20?limit=200&order_by=block_timestamp,asc{extra}'+(f'&fingerprint={fp}' if fp else '')
        r=http(url,headers=H,cache=True,min_gap=0.4)
        rows+=r.get('data',[]); fp=r.get('meta',{}).get('fingerprint')
        if not fp: break
    return rows, bool(fp)
def T(ms): return dt.datetime.fromtimestamp(ms/1000,dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
def summ(a, t0=None, t1=None, show=25, maxpages=10, **kw):
    rows,more=trc20(a,maxpages,**kw)
    acc=http(f'https://api.trongrid.io/v1/accounts/{a}',headers=H,cache=True,min_gap=0.4)
    d=(acc.get('data') or [{}])[0]
    print(f'### TRON {a} created={T(d.get("create_time",0)) if d else None} trx={d.get("balance",0)/1e6 if d else 0} trc20rows={len(rows)}{"+ (truncated)" if more else ""}')
    ins=Counter(); outs=Counter()
    for x in rows:
        amt=int(x['value'])/10**int(x['token_info']['decimals'])
        if x['to']==a: ins[x['from']]+=1
        else: outs[x['to']]+=1
    print('   distinct senders',len(ins),'top',ins.most_common(4)); print('   distinct recipients',len(outs),'top',outs.most_common(4))
    n=0
    for x in rows:
        if t0 and x['block_timestamp']<t0*1000: continue
        if t1 and x['block_timestamp']>t1*1000: continue
        amt=int(x['value'])/10**int(x['token_info']['decimals'])
        if amt<1: continue
        print(f"   {T(x['block_timestamp'])} {'IN ' if x['to']==a else 'OUT'} {x['token_info']['symbol']:5s} {amt:>12,.2f} {x['from'] if x['to']==a else x['to']} {x['transaction_id']}")
        n+=1
        if n>=show: break
    return rows
if __name__=='__main__':
    a=sys.argv[1]; t0=int(sys.argv[2]) if len(sys.argv)>2 else None; t1=int(sys.argv[3]) if len(sys.argv)>3 else None
    summ(a,t0,t1)
