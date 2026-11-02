import sys,json,os,statistics,datetime as dt; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common2 import http, es
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
EVENTS={'maduro':dict(title='Maduro out by January 31, 2026?',t0=1767416400,t1=1767420720,tmove=None),
        'iran':dict(title='US strikes Iran by February 28, 2026?',t0=1772256480,t1=1772259180,tmove=None)}
PS=json.load(open('price_series.json')); MK=json.load(open('markets.json'))
EVENTS['maduroX']=dict(title='Maduro out by January 31, 2026?',t0=1767333600,t1=1767416400,tmove=None)
EVENTS['iranA']=dict(title='US strikes Iran by February 28, 2026?',t0=1772139600,t1=1772148600,tmove=None)
EVENTS['iranB']=dict(title='US strikes Iran by February 28, 2026?',t0=1772202600,t1=1772214300,tmove=None)
EVENTS['maduroX']['tmove']=PS['Maduro out by January 31, 2026?']['t_1p5x']; EVENTS['iranA']['tmove']=EVENTS['iranB']['tmove']=PS['US strikes Iran by February 28, 2026?']['t_1p5x']
EVENTS['maduro']['tmove']=PS['Maduro out by January 31, 2026?']['t_1p5x']; EVENTS['iran']['tmove']=PS['US strikes Iran by February 28, 2026?']['t_1p5x']
NETWORK={'0x168b100d7a6620a2f49a455344c2c006eaf1714b':'Chiwawas','0x834079f62fa9b4b0bdfad5b8b7a841e8267da024':'chileno777','0x5621116629c5d640c8186f577362478cc6605245':'TacticalInsiderNews',
 '0xbf32f7a77ccea8bba647fea63d438ce1778b1762':'154x838hjd6','0x56efadc9defe5b7a21af751e0d026f2cf54136db':'Neodbs','0x38745db27f7360a287f6ca3c9b6a6a9c76149801':'Planktonbets',
 '0xe9b80c387ba77a585423b13c850c2e126c3befd8':'Mrs.Joker','0x60280beffdfeaf962de4e6397ab49ed05a1b99e1':'X34'}
JULY={'0x6baf05d193692bb208d616709e27442c910a94c5':'SBet365','0x31a56e9e690c621ed21de08cb559e9524cdb8ed9':'0x31a56e9e','0xa72db1749e9ac2379d49a3c12708325ed17febd4':'0xa72db1749e','0x0e9310b9a1bf61ff13d5a31e8ca6188abc8ddb0c':'LINKCS'}
PM_INTERNAL={'0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e','0x4d97dcd97ec945f40cf65f87097ace5ea0476045','0xc5d563a36ae78145c45a50134d48a1215220f80a','0x3a3bd7bb9528e159577f7c2e685cc81a765002e2','0xd91e80cf2e7be2e162c6513ced06f1dd0da35296','0x78769d50be1763ed1ca0d5e878d93f05aabff29e'}
RELAY={'0xf70da97812cb96acdf810712aa562db8dfa3dbef','0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222','0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb','0x56c262027e0de4aea31d2489529cb25d23e58a8b','0xa5a5491bca93dd4c076e4906e79e7673f4a5a142','0x4cd00e387622c35bddb9b4c962c136462338bc31'}
POL_ST={'0x2791bca1f2de4661ed88a30c99a7a9449aa84174':'USDC.e','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':'USDC','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb':'pUSD'}
# graph nodes (non infra, non high)
G=set()
if os.path.exists('bfs2/nodes.jsonl'):
    for l in open('bfs2/nodes.jsonl'):
        n=json.loads(l)
        if n.get('kind') in ('EVM','PM','TRON') and 'HIGH' not in n.get('flags',[]): G.add(n['addr'])
G|=set(NETWORK)
# block interpolation grid (Polygon)
_grid={}
def pblk(t):
    step=43200; t0=(t//step)*step
    for tt in (t0,t0+step):
        if tt not in _grid:
            fp=f'cache/pblk_{tt}.json'
            if os.path.exists(fp): _grid[tt]=json.load(open(fp))
            else: _grid[tt]=int(es(137,module='block',action='getblocknobytime',timestamp=tt,closest='before')); json.dump(_grid[tt],open(fp,'w'))
    b0,b1=_grid[t0],_grid[t0+step]
    return int(b0+(b1-b0)*(t-t0)/step)
def relay_dec(h):
    try:
        d=http(f'https://api.relay.link/requests/v2?hash={h}',cache=True); q=(d.get('requests') or [None])[0]
    except Exception: return None
    if not q: return None
    m=q['data'].get('metadata',{})
    return dict(user=(q.get('user') or '').lower() if (q.get('user') or '').startswith('0x') else q.get('user'),recip=(q.get('recipient') or '').lower() if (q.get('recipient') or '').startswith('0x') else q.get('recipient'),
                inChain=m.get('currencyIn',{}).get('currency',{}).get('chainId'),outChain=m.get('currencyOut',{}).get('currency',{}).get('chainId'),inSym=m.get('currencyIn',{}).get('currency',{}).get('symbol'))
def market_activity(w,cid):
    rows=[]; off=0
    while True:
        d=http(f'https://data-api.polymarket.com/activity?user={w}&market={cid}&limit=500&offset={off}',cache=True)
        if not isinstance(d,list): break
        rows+=d
        if len(d)<500 or off>=3000: break
        off+=500
    return rows, off>=3000
def flows(w, t_a, t_b):
    rows=[]
    for p in range(1,4):
        r=es(137,module='account',action='tokentx',address=w,startblock=pblk(t_a),endblock=pblk(t_b),sort='asc',page=p,offset=1000)
        rows+=r
        if len(r)<1000: break
    out=[]
    for x in rows:
        c=x['contractAddress'].lower()
        if c not in POL_ST: continue
        amt=int(x['value'])/1e6
        if amt<1: continue
        d='IN' if x['to'].lower()==w else 'OUT'; cp=(x['from'] if d=='IN' else x['to']).lower()
        if cp in PM_INTERNAL: continue
        out.append(dict(ts=int(x['timeStamp']),dir=d,sym=POL_ST[c],amt=amt,cp=cp,tx=x['hash']))
    return out, len(rows)>=3000
def analyse_wallet(w, ev, buys):
    E=EVENTS[ev]; cid=MK[E['title']]['conditionId']; yes=MK[E['title']]['tokens']['Yes']
    first=min(b['ts'] for b in buys)
    res=dict(wallet=w,event=ev,first_buy=first,n_orders=len(set(b['tx'] for b in buys)),capital=sum(b['usdc'] for b in buys),shares=sum(b['shares'] for b in buys))
    res['vwap']=res['capital']/res['shares'] if res['shares'] else None
    res['min_price']=min(b['usdc']/b['shares'] for b in buys if b['shares'])
    res['delay_to_move_s']=E['tmove']-first
    try:
        act,capped=market_activity(w,cid); res['activity_capped']=capped
        c=defaultdict(float)
        for a in act:
            k=a['type'] if a['type']!='TRADE' else a['side']; c[k]+=float(a.get('usdcSize') or 0)
        pos=http(f'https://data-api.polymarket.com/positions?user={w}&market={cid}&sizeThreshold=0',cache=True)
        cur=sum(float(x.get('currentValue') or 0) for x in pos) if isinstance(pos,list) else 0
        res.update(mkt_BUY=c['BUY'],mkt_SELL=c['SELL'],mkt_REDEEM=c['REDEEM'],mkt_MERGE=c['MERGE'],mkt_SPLIT=c['SPLIT'],mkt_CUR=cur)
        res['mkt_PnL']=c['SELL']+c['REDEEM']+c['MERGE']+cur-c['BUY']-c['SPLIT']
        res['held']= (c['REDEEM']>0) or (cur>0)
        res['name']=act[0].get('name') if act else None
        res['total_rows_first']=None
    except Exception as e: res['mkt_err']=str(e)[:100]
    # window-buy value at resolution (YES won => $1/share)
    res['window_value_at_res']=res['shares']-res['capital']
    # funding & withdrawals
    try:
        fl,capf=flows(w, first-7*86400, first+14*86400); res['flows_capped']=capf
        ins=[f for f in fl if f['dir']=='IN' and f['ts']<=first]
        outs=[f for f in fl if f['dir']=='OUT' and f['ts']>first]
        srcs=[]
        for f in ins[-6:]:
            s=dict(ts=f['ts'],amt=f['amt'],cp=f['cp'],tx=f['tx'])
            if f['cp'] in RELAY or f['cp']=='0x0000000000000000000000000000000000000000':
                r=relay_dec(f['tx'])
                if r: s.update(via='relay',origin_user=r['user'],origin_chain=r['inChain'],asset=r['inSym'])
                else: s['via']='relay?/mint' if f['cp'] in RELAY else 'mint(0x0)'
            else: s['via']='direct'
            srcs.append(s)
        dsts=[]
        for f in outs[:8]:
            s=dict(ts=f['ts'],amt=f['amt'],cp=f['cp'],tx=f['tx'])
            if f['cp'] in RELAY:
                r=relay_dec(f['tx'])
                if r: s.update(via='relay',dest=r['recip'],dest_chain=r['outChain'])
            else: s['via']='direct'
            dsts.append(s)
        res['funding']=srcs; res['withdrawals']=dsts
        res['last_fund_ts']=max((s['ts'] for s in srcs),default=None)
        res['funding_latency_s']=(first-res['last_fund_ts']) if res['last_fund_ts'] else None
        res['funding_identifiable']=bool(srcs)
        cps=set()
        for s in srcs: cps|={s.get('cp'),s.get('origin_user')}
        for s in dsts: cps|={s.get('cp'),s.get('dest')}
        cps.discard(None)
        res['graph_links']=sorted(c for c in cps if c in G and c!=w)
    except Exception as e: res['flow_err']=str(e)[:100]
    res['network']=NETWORK.get(w); res['july']=JULY.get(w)
    return res
def buyers(ev):
    E=EVENTS[ev]; by=defaultdict(list)
    for l in open(f'fills_{ev}.jsonl'):
        x=json.loads(l)
        if '_range' in x: continue
        if x['mAsset']=='USDC' and x['tAsset']=='Yes' and E['t0']<=x['ts']<E['t1']:
            by[x['maker'].lower()].append(dict(ts=x['ts'],usdc=x['mAmt'],shares=x['tAmt'],tx=x['tx']))
    return by
if __name__=='__main__':
    ev=sys.argv[1]; by=buyers(ev)
    print(ev,'buyers',len(by),'fills',sum(len(v) for v in by.values()),flush=True)
    out=[]
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(lambda kv: analyse_wallet(kv[0],ev,kv[1]), by.items()):
            out.append(r)
            if len(out)%50==0: print(len(out),flush=True)
    json.dump(out,open(f'pop_{ev}.json','w'),indent=1)
    print('done',len(out))
