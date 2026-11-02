import sys,json,os,datetime as dt; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common2 import http
from collections import defaultdict
USDT='TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
BR='TPwezUWpEGmFBENNWJHwXHRG1D2NCEEt5s'; RL='TXtEs6t2oUWQsNos7m68gbHdE9Q5n6x2oN'
def T(ms): return dt.datetime.fromtimestamp(ms/1000,dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
def pages(a, maxpages, extra=''):
    rows=[]; fp=None; more=False
    for i in range(maxpages):
        r=http(f'https://api.trongrid.io/v1/accounts/{a}/transactions/trc20?limit=200&contract_address={USDT}&order_by=block_timestamp,asc{extra}'+(f'&fingerprint={fp}' if fp else ''),cache=True)
        rows+=r.get('data',[]); fp=r.get('meta',{}).get('fingerprint')
        if not fp: break
        if i==maxpages-1: more=True
    return rows,more
def deep(a, maxpages=15, extra=''):
    acc=http(f'https://api.trongrid.io/v1/accounts/{a}',cache=True); d=(acc.get('data') or [{}])[0]
    rows,more=pages(a,maxpages,extra)
    last=http(f'https://api.trongrid.io/v1/accounts/{a}/transactions/trc20?limit=1&contract_address={USDT}&order_by=block_timestamp,desc',cache=True).get('data',[])
    inn=defaultdict(float); out=defaultdict(float); nin=defaultdict(int); nout=defaultdict(int); tin=tout=0.0
    for x in rows:
        v=int(x['value'])/1e6
        if v>1e11 or x.get('type')!='Transfer': continue
        if x['to']==a: inn[x['from']]+=v; nin[x['from']]+=1; tin+=v
        if x['from']==a: out[x['to']]+=v; nout[x['to']]+=1; tout+=v
    res=dict(addr=a, created=T(d.get('create_time',0)) if d else None, first=T(rows[0]['block_timestamp']) if rows else None,
             last=T(last[0]['block_timestamp']) if last else None, n=len(rows), truncated=more, usdt_in=round(tin,2), usdt_out=round(tout,2),
             n_senders=len(inn), n_recipients=len(out), top_in=sorted(((k,round(v,2),nin[k]) for k,v in inn.items()),key=lambda z:-z[1])[:8],
             top_out=sorted(((k,round(v,2),nout[k]) for k,v in out.items()),key=lambda z:-z[1])[:8],
             bridgers_in=round(inn.get(BR,0),2), bridgers_out=round(out.get(BR,0),2), relay_out=round(out.get(RL,0),2),
             sweep_share=round(max(out.values())/tout,3) if tout else None)
    return res
if __name__=='__main__':
    R={}
    for a in ['TSahUmP5mWriKP7ftbkLvz6AJ8zvc5qTPT','TJs1u6k8RWaqgLRZTxF9eKXojWv8HsbJwx','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf','TA4chMztaY6TW8dv7qnuqmJKvb4edZqwj5','TDG9T4FwwwBfYBkRtb1DCcAbjNGj2WTpNi','TChkscPd95MexmFGZLWpSLkrNnyfg8V2rE','TEfE77WkNAzm6DrKhkqd6S9kw53HnqHPS6','TFMhN2unzoVHvyxQZ7FAt3UuKXCbegpekp','TLREUZVRJ9jifQfKvnDMRyXxEhasiGYhP4']:
        R[a]=deep(a); print(json.dumps(R[a])[:900]); print()
    # TDqSquXB: high volume -> windows around the two sweeps into it
    R['TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf']=deep('TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf',maxpages=5,extra=f'&min_timestamp={1767470000*1000}&max_timestamp={1767490000*1000}')
    print(json.dumps(R['TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf'])[:900])
    json.dump(R,open('tron_deep.json','w'),indent=1)
