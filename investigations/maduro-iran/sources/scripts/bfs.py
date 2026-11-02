import sys,json,re,datetime as dt; sys.path.insert(0,'.')
from common import *
from relay_user import relay_by_user
from tron import trc20
from collections import defaultdict, deque
T0=1764547200  # 2025-12-01
T1=1775000000  # 2026-03-31
def isevm(a): return a.startswith('0x') and len(a)==42
def istron(a): return a.startswith('T') and len(a)==34
INFRA={'0xf70da97812cb96acdf810712aa562db8dfa3dbef','0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222','0x4cd00e387622c35bddb9b4c962c136462338bc31','0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb','0xb685760ebd368a891f27ae547391f4e2a289895b','0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e','0x4d97dcd97ec945f40cf65f87097ace5ea0476045','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb','0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae','0x0000000000000000000000000000000000000000','0xa5a5491bca93dd4c076e4906e79e7673f4a5a142','0x56c262027e0de4aea31d2489529cb25d23e58a8b',
       'TPwezUWpEGmFBENNWJHwXHRG1D2NCEEt5s','TXtEs6t2oUWQsNos7m68gbHdE9Q5n6x2oN'}
edges=[]  # (src,dst,chain,amt,sym,ts,tx,kind)
def add(*e): edges.append(e)
pm_cache={}
def pm_count(a):
    if a in pm_cache: return pm_cache[a]
    d=http(f'https://data-api.polymarket.com/activity?user={a}&limit=5',cache=True,min_gap=0.2)
    pm_cache[a]=len(d) if isinstance(d,list) else -1
    return pm_cache[a]
def relay_edges(a):
    out=[]
    for q in relay_by_user(a):
        m=q['data'].get('metadata',{}); ci=m.get('currencyIn',{}); co=m.get('currencyOut',{})
        ts=int(dt.datetime.fromisoformat(q['createdAt'].replace('Z','+00:00')).timestamp())
        if q.get('status')!='success': continue
        u=q['user']; r=q['recipient']
        u=u.lower() if isevm(u) else u; r=r.lower() if isevm(r) else r
        amt=float(ci.get('amountUsd') or ci.get('amountFormatted') or 0)
        out.append((u,r,f"{ci.get('currency',{}).get('chainId')}->{co.get('currency',{}).get('chainId')}",amt,ci.get('currency',{}).get('symbol'),ts,q['id'],'relay'))
    return out
if __name__=='__main__':
    seeds=sys.argv[1:]
    seen=set(); q=deque((s,0) for s in seeds); MAXD=3
    info={}
    while q and len(seen)<250:
        a,d=q.popleft()
        if a in seen or a in INFRA: continue
        seen.add(a)
        nb=set()
        try:
            for e in relay_edges(a):
                add(*e); nb.add(e[0]); nb.add(e[1])
        except Exception as ex: print('relay err',a,ex)
        kind='?'
        if istron(a):
            rows,more=trc20(a,maxpages=3)
            if more or len(rows)>=500: kind='TRON_HIGHDEG'; info[a]=kind; continue
            kind='TRON'
            for x in rows:
                if x['token_info']['symbol'] not in ('USDT','USDC') : continue
                amt=int(x['value'])/10**int(x['token_info']['decimals'])
                if amt<100 or amt>1e12: continue
                ts=x['block_timestamp']//1000
                if not (T0<=ts<=T1): continue
                add(x['from'],x['to'],'tron',amt,x['token_info']['symbol'],ts,x['transaction_id'],'trc20')
                nb.add(x['from']); nb.add(x['to'])
        elif isevm(a):
            n=pm_count(a)
            if n>0: kind='PM'
            else:
                nonce=es(1,module='proxy',action='eth_getTransactionCount',address=a,tag='latest')
                nonce=int(nonce['result'],16) if isinstance(nonce,dict) and nonce.get('result') else 0
                kind=f'EOA(n={nonce})'
                if nonce>300: info[a]='EVM_HIGHDEG'; continue
                OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7'}
                tt=es(1,module='account',action='tokentx',address=a,startblock=0,endblock=99999999,sort='asc',page=1,offset=1000)
                for x in tt:
                    if x['contractAddress'].lower() not in OFF: continue
                    amt=int(x['value'])/1e6; ts=int(x['timeStamp'])
                    if amt<100 or not (T0<=ts<=T1): continue
                    add(x['from'].lower(),x['to'].lower(),'eth',amt,x['tokenSymbol'],ts,x['hash'],'erc20')
                    nb.add(x['from'].lower()); nb.add(x['to'].lower())
                # gas edges: native from low-degree EOAs
                tx=es(1,module='account',action='txlist',address=a,startblock=0,endblock=99999999,sort='asc',page=1,offset=200)
                for x in tx:
                    if int(x['value'])>0 and x['isError']=='0':
                        add(x['from'].lower(),x['to'].lower(),'eth',int(x['value'])/1e18,'ETH',int(x['timeStamp']),x['hash'],'native')
                        nb.add(x['from'].lower()); nb.add(x['to'].lower())
        info[a]=kind
        print(f'd={d} {kind:14s} {a} nb={len(nb)}',flush=True)
        if d<MAXD:
            for b in nb:
                if b not in seen and b not in INFRA: q.append((b,d+1))
    json.dump(dict(edges=edges,info=info),open('bfs_out.json','w'))
    print('nodes',len(seen),'edges',len(edges))
