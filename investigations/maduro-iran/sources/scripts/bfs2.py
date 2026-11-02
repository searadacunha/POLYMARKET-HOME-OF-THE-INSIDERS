import sys, os, json, time, datetime as dt, threading, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common2 import http, es
W0,W1=1764547200,1775001600            # 2025-12-01 .. 2026-04-01 UTC
OUT='bfs2'; os.makedirs(OUT,exist_ok=True)
ETH_ST={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':('USDC',6),'0xdac17f958d2ee523a2206206994597c13d831ec7':('USDT',6)}
POL_ST={'0x2791bca1f2de4661ed88a30c99a7a9449aa84174':('USDC.e',6),'0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':('USDC',6),'0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb':('pUSD',6),'0xc2132d05d31c914a87c6611c10748aeb04b58e8f':('USDT0',6)}
TRON_ST={'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t':'USDT','TEkxiTehnzSmSe2XqrBj4w32RUN966rdz8':'USDC'}
INFRA={ # role labels; recorded as nodes, never expanded, never counted as control evidence
 '0xf70da97812cb96acdf810712aa562db8dfa3dbef':'Relay solver','0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222':'RelayRouter','0x4cd00e387622c35bddb9b4c962c136462338bc31':'Relay depository/intake',
 '0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb':'Relay (receiver)','0x56c262027e0de4aea31d2489529cb25d23e58a8b':'Relay (receiver)','0xa5a5491bca93dd4c076e4906e79e7673f4a5a142':'Relay (receiver)',
 '0xb685760ebd368a891f27ae547391f4e2a289895b':'Bridgers ETH','TPwezUWpEGmFBENNWJHwXHRG1D2NCEEt5s':'Bridgers TRON payout','TXtEs6t2oUWQsNos7m68gbHdE9Q5n6x2oN':'Relay TRON deposit',
 '0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e':'CTFExchange','0xc5d563a36ae78145c45a50134d48a1215220f80a':'NegRisk CTFExchange','0x4d97dcd97ec945f40cf65f87097ace5ea0476045':'ConditionalTokens',
 '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb':'pUSD','0x3a3bd7bb9528e159577f7c2e685cc81a765002e2':'WrappedCollateral','0xe111180000d2663c0091e4f400237545b87b996b':'PM exchange (pUSD)',
 '0xab19716584931d81cd9e7763402673a64baa4876':'PM exchange (pUSD)','0x5d0f03cf1243a3e21262d6cf844795afd9fff0ad':'PM exchange (pUSD)','0xc417fd8e9661c0d2120b64a04bb3278c17e99db1':'PM USDC.e custody',
 '0x0000000000000000000000000000000000000000':'mint/burn','0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae':'LI.FI Diamond'}
def isevm(a): return isinstance(a,str) and a.startswith('0x') and len(a)==42
def istron(a): return isinstance(a,str) and a.startswith('T') and len(a)==34
def issol(a): return isinstance(a,str) and not a.startswith('0x') and not istron(a) and 32<=len(a)<=44
def norm(a): return a.lower() if isevm(a) else a
lock=threading.Lock()
EF=open(os.path.join(OUT,'edges.jsonl'),'a'); NF=open(os.path.join(OUT,'nodes.jsonl'),'a')
def emit_edges(rows):
    with lock:
        for r in rows: EF.write(json.dumps(r)+'\n')
        EF.flush()
def emit_node(n):
    with lock: NF.write(json.dumps(n)+'\n'); NF.flush()
_blk={}
def blk(chain,t,closest):
    k=(chain,t,closest)
    if k not in _blk: _blk[k]=int(es(chain,module='block',action='getblocknobytime',timestamp=t,closest=closest))
    return _blk[k]
def pm_count(a):
    d=http(f'https://data-api.polymarket.com/activity?user={a}&limit=3',cache=True)
    return len(d) if isinstance(d,list) else -1
def relay_edges(a, maxpages=10):
    out=[]; cont=None; n=0
    for i in range(maxpages):
        url=f'https://api.relay.link/requests/v2?user={a}&limit=50'+(f'&continuation={cont}' if cont else '')
        d=http(url,cache=True); rq=d.get('requests',[]); n+=len(rq)
        for q in rq:
            if q.get('status')!='success': continue
            m=q['data'].get('metadata',{}); ci=m.get('currencyIn',{}); co=m.get('currencyOut',{})
            ts=int(dt.datetime.fromisoformat(q['createdAt'].replace('Z','+00:00')).timestamp())
            ins=[t.get('hash') for t in q['data'].get('inTxs',[])]; outs=[t.get('hash') for t in q['data'].get('outTxs',[])]
            amt=ci.get('amountUsd') or ci.get('amountFormatted')
            out.append(dict(src=norm(q['user']),dst=norm(q['recipient']),chain=f"{ci.get('currency',{}).get('chainId')}->{co.get('currency',{}).get('chainId')}",
                asset=f"{ci.get('currency',{}).get('symbol')}->{co.get('currency',{}).get('symbol')}",amt=float(amt or 0),ts=ts,tx=f"{ins[0] if ins else ''}|{outs[0] if outs else ''}",kind='relay',rid=q.get('id'),obs=a))
        cont=d.get('continuation')
        if not cont or not rq: break
    return out, n
def evm_token_edges(chain, a, sb, eb, stables, maxpages=3):
    rows=[]; full=False
    for p in range(1,maxpages+1):
        r=es(chain,module='account',action='tokentx',address=a,startblock=sb,endblock=eb,sort='asc',page=p,offset=1000)
        for x in r:
            c=x['contractAddress'].lower()
            if c not in stables: continue
            sym,dec=stables[c]; amt=int(x['value'])/10**dec
            if amt<10: continue
            rows.append(dict(src=x['from'].lower(),dst=x['to'].lower(),chain=str(chain),asset=sym,amt=amt,ts=int(x['timeStamp']),tx=x['hash'],kind='erc20',obs=a))
        if len(r)<1000: break
        if p==maxpages: full=True
    return rows, full
def evm_native_edges(chain,a,sb,eb):
    rows=[]
    r=es(chain,module='account',action='txlist',address=a,startblock=sb,endblock=eb,sort='asc',page=1,offset=1000)
    for x in r:
        if int(x['value'])>0 and x.get('isError','0')=='0':
            rows.append(dict(src=x['from'].lower(),dst=(x['to'] or '').lower(),chain=str(chain),asset='NATIVE',amt=int(x['value'])/1e18,ts=int(x['timeStamp']),tx=x['hash'],kind='native',obs=a))
    return rows, len(r)>=1000
def tron_edges(a, t0, t1, maxpages=5):
    rows=[]; fp=None; full=False; npg=0
    for i in range(maxpages):
        url=f'https://api.trongrid.io/v1/accounts/{a}/transactions/trc20?limit=200&order_by=block_timestamp,asc&min_timestamp={t0*1000}&max_timestamp={t1*1000}'+(f'&fingerprint={fp}' if fp else '')
        r=http(url,cache=True); npg+=1
        for x in r.get('data',[]):
            if x.get('type')!='Transfer': continue
            tok=x['token_info']['address']
            if tok not in TRON_ST: continue
            amt=int(x['value'])/10**int(x['token_info']['decimals'])
            if amt<10 or amt>1e11: continue
            rows.append(dict(src=x['from'],dst=x['to'],chain='tron',asset=TRON_ST[tok],amt=amt,ts=x['block_timestamp']//1000,tx=x['transaction_id'],kind='trc20',obs=a))
        fp=r.get('meta',{}).get('fingerprint')
        if not fp: break
        if i==maxpages-1: full=True
    # native TRX (gas/energy funding)
    try:
        r=http(f'https://api.trongrid.io/v1/accounts/{a}/transactions?limit=200&only_confirmed=true&min_timestamp={t0*1000}&max_timestamp={t1*1000}',cache=True)
        import base58check_stub
    except Exception: pass
    return rows, full
# TRX native via hex->base58
import hashlib
ALPH='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def hex2b58(h):
    b=bytes.fromhex(h); chk=hashlib.sha256(hashlib.sha256(b).digest()).digest()[:4]; n=int.from_bytes(b+chk,'big'); s=''
    while n: n,r=divmod(n,58); s=ALPH[r]+s
    return s
def tron_native(a,t0,t1):
    rows=[]
    try: r=http(f'https://api.trongrid.io/v1/accounts/{a}/transactions?limit=200&only_confirmed=true&min_timestamp={t0*1000}&max_timestamp={t1*1000}',cache=True)
    except Exception: return rows
    for x in r.get('data',[]):
        try:
            c=x['raw_data']['contract'][0]
            if c['type']!='TransferContract': continue
            v=c['parameter']['value']; amt=v['amount']/1e6
            if amt<1: continue
            rows.append(dict(src=hex2b58(v['owner_address']),dst=hex2b58(v['to_address']),chain='tron',asset='TRX',amt=amt,ts=x['block_timestamp']//1000,tx=x['txID'],kind='native',obs=a))
        except Exception: pass
    return rows
KNOWN=set()
def windows_around(ts_list, pad=7200):
    iv=sorted((max(W0,t-pad),min(W1,t+pad)) for t in ts_list)
    m=[]
    for s,e in iv:
        if m and s<=m[-1][1]: m[-1]=(m[-1][0],max(m[-1][1],e))
        else: m.append((s,e))
    return m[:25]
INTER={}  # addr -> list of ts where known nodes interacted with it
def process(a, depth):
    node=dict(addr=a,depth=depth,kind='?',flags=[])
    try:
        if a in INFRA:
            node['kind']='INFRA'; node['label']=INFRA[a]; emit_node(node); return node,[]
        rows=[]
        try:
            rr,nrel=relay_edges(a); rows+=rr; node['relay_orders']=nrel
        except Exception as e: node['flags'].append('relay_err')
        if isevm(a):
            n=pm_count(a); node['pm_rows']=n
            nonce=es(1,module='proxy',action='eth_getTransactionCount',address=a,tag='latest')
            node['nonce_eth']=int(nonce['result'],16) if isinstance(nonce,dict) and nonce.get('result') else None
            high=False
            for chain,st in ((1,ETH_ST),(137,POL_ST)):
                sb,eb=blk(chain,W0,'after'),blk(chain,W1,'before')
                tr,full=evm_token_edges(chain,a,sb,eb,st)
                nr,nfull=evm_native_edges(chain,a,sb,eb) if chain==1 else ([],False)
                if full or nfull: high=True
                rows+=tr+nr
                node[f'n_{chain}']=len(tr)+len(nr)
            if (node['nonce_eth'] or 0)>300: high=True
            node['kind']='PM' if n>0 else 'EVM'
            if high: node['flags'].append('HIGH')
        elif istron(a):
            if depth>=2:
                tr,full=tron_edges(a,W0,W1,maxpages=1); rows+=tr; node['flags'].append('light')
            else:
                tr,full=tron_edges(a,W0,W1); rows+=tr; rows+=tron_native(a,W0,W1)
            node['kind']='TRON'; node['n_tron']=len(tr)
            if full: node['flags'].append('HIGH')
        elif issol(a):
            node['kind']='SOL'; node['flags'].append('not_expanded_here')
        # HIGH: keep only edges touching KNOWN nodes (targeted), counts kept
        if 'HIGH' in node['flags']:
            cps=set((r['dst'] if r['src']==a else r['src']) for r in rows)
            node['distinct_cp_sample']=len(cps)
            wins=windows_around(INTER.get(a,[]), pad=21600) if not (depth>=2 and istron(a)) else []
            node['targeted_windows']=len(wins)
            for (s0,e0) in wins:
                try:
                    if isevm(a):
                        for chain,st in ((1,ETH_ST),(137,POL_ST)):
                            tr,_=evm_token_edges(chain,a,blk(chain,s0,'after'),blk(chain,e0,'before'),st,maxpages=2); rows+=tr
                        nr,_=evm_native_edges(1,a,blk(1,s0,'after'),blk(1,e0,'before')); rows+=nr
                    elif istron(a):
                        tr,_=tron_edges(a,s0,e0,maxpages=3); rows+=tr
                except Exception as e: node['flags'].append('targeted_err')
            seen=set(); ded=[]
            for r in rows:
                k=(r['tx'],r['src'],r['dst'],round(r['amt'],6))
                if k in seen: continue
                seen.add(k); ded.append(r)
            rows=ded
            rows=[r for r in rows if (r['dst'] if r['src']==a else r['src']) in KNOWN or r['kind']=='relay']
        emit_edges(rows); emit_node(node)
        return node, rows
    except Exception as e:
        node['kind']='ERR'; node['err']=str(e)[:200]; emit_node(node); return node,[]
if __name__=='__main__':
    seeds=[norm(s) for s in sys.argv[1:]]
    done={}
    nfile=os.path.join(OUT,'nodes.jsonl')
    if os.path.exists(nfile):
        for l in open(nfile):
            try: n=json.loads(l); done[n['addr']]=n
            except: pass
    edges=[]
    efile=os.path.join(OUT,'edges.jsonl')
    if os.path.exists(efile):
        for l in open(efile):
            try: edges.append(json.loads(l))
            except: pass
    from collections import defaultdict
    def neigh(a, rows):
        s=set()
        for r in rows:
            b=r['dst'] if r['src']==a else (r['src'] if r['dst']==a else None)
            if b and b!=a: s.add(b)
        return s
    level={s:0 for s in seeds}; frontier=list(seeds)
    KNOWN.update(seeds)
    MAXD=2
    for d in range(MAXD+1):
        INTER.clear()
        for r in edges:
            INTER.setdefault(r['src'],[]).append(r['ts']); INTER.setdefault(r['dst'],[]).append(r['ts'])
        todo=[a for a in frontier if a not in done or done[a].get('kind')=='ERR']
        print(f'=== depth {d}: frontier {len(frontier)} todo {len(todo)}',flush=True)
        res={}
        with ThreadPoolExecutor(12) as ex:
            futs={ex.submit(process,a,d):a for a in todo}
            k=0
            for f in as_completed(futs):
                a=futs[f]; node,rows=f.result(); done[a]=node; edges+=rows; k+=1
                if k%50==0: print(f'   {k}/{len(todo)}',flush=True)
        # next frontier
        nxt=set()
        byaddr=defaultdict(list)
        for r in edges: byaddr[r['src']].append(r); byaddr[r['dst']].append(r)
        for a in frontier:
            n=done.get(a,{})
            if n.get('kind')=='INFRA': continue
            for b in neigh(a,byaddr[a]):
                if b not in level: level[b]=d+1; nxt.add(b)
        KNOWN.update(nxt)
        frontier=sorted(nxt)
        if d==MAXD:
            json.dump(dict(level=level),open(os.path.join(OUT,'levels.json'),'w'))
            print('depth3 (recorded, not processed):',len(frontier))
    print('DONE nodes',len(done),'edges',len(edges),flush=True)
