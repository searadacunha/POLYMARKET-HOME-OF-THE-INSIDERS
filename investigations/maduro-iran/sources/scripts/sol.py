import sys,json,datetime as dt; sys.path.insert(0,'.')
from common import *
HK=ENV['HELIUS_KEY']
USDC='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'; USDT='Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
def T(t): return dt.datetime.fromtimestamp(int(t),dt.UTC).strftime('%Y-%m-%d %H:%M:%S')
def txs(a,maxpages=10,before=None):
    out=[]
    for i in range(maxpages):
        url=f'https://api.helius.xyz/v0/addresses/{a}/transactions?api-key={HK}&limit=100'+(f'&before={before}' if before else '')
        d=http(url,cache=True,min_gap=0.25)
        if not isinstance(d,list): raise RuntimeError(str(d)[:200])
        out+=d
        if len(d)<100: break
        before=d[-1]['signature']
    return out
def sigcount(a,maxpages=5):
    n=0; before=None
    for i in range(maxpages):
        body={'jsonrpc':'2.0','id':1,'method':'getSignaturesForAddress','params':[a,{'limit':1000}|({'before':before} if before else {})]}
        d=http(ENV['HELIUS_RPC_URL'],data=body,cache=True,min_gap=0.2)
        r=d.get('result',[]); n+=len(r)
        if len(r)<1000: return n, (r[-1]['blockTime'] if r else None), False
        before=r[-1]['signature']
    return n,None,True
def flows(a,t0=None,t1=None,minusd=1,maxpages=10,show=40):
    tx=txs(a,maxpages)
    rows=[]
    for x in tx:
        for tt in x.get('tokenTransfers',[]):
            if tt['mint'] not in (USDC,USDT): continue
            if a not in (tt.get('fromUserAccount'),tt.get('toUserAccount')): continue
            d='IN ' if tt.get('toUserAccount')==a else 'OUT'
            cp=tt.get('fromUserAccount') if d=='IN ' else tt.get('toUserAccount')
            rows.append((x['timestamp'],d,'USDC' if tt['mint']==USDC else 'USDT',tt['tokenAmount'],cp,x['signature'],x.get('source'),x.get('type')))
        for nt in x.get('nativeTransfers',[]):
            if a not in (nt.get('fromUserAccount'),nt.get('toUserAccount')): continue
            if nt['amount']<1e7: continue
            d='IN ' if nt.get('toUserAccount')==a else 'OUT'
            cp=nt.get('fromUserAccount') if d=='IN ' else nt.get('toUserAccount')
            rows.append((x['timestamp'],d,'SOL',nt['amount']/1e9,cp,x['signature'],x.get('source'),x.get('type')))
    rows.sort()
    n,oldest,trunc=sigcount(a)
    print(f'### SOL {a} sigs={n}{"+" if trunc else ""} oldest_in_window={T(oldest) if oldest else None} helius_tx={len(tx)}')
    k=0
    for r in rows:
        if t0 and r[0]<t0: continue
        if t1 and r[0]>t1: continue
        if r[2]!='SOL' and r[3]<minusd: continue
        print(f'   {T(r[0])} {r[1]} {r[2]:4s} {r[3]:>14,.4f} {r[4]} {r[6]}/{r[7]} {r[5][:20]}')
        k+=1
        if k>=show: print('   ...'); break
    return rows
if __name__=='__main__':
    a=sys.argv[1]; t0=int(sys.argv[2]) if len(sys.argv)>2 else None; t1=int(sys.argv[3]) if len(sys.argv)>3 else None
    flows(a,t0,t1)
