import os, json, time, hashlib, urllib.request, urllib.parse
ENV={}
for p in [os.path.expanduser('~/Downloads/.env'), os.path.expanduser('~/Downloads/.env.local')]:
    for l in open(p):
        l=l.strip()
        if l and not l.startswith('#') and '=' in l:
            k,v=l.split('=',1); ENV[k.strip()]=v.strip().strip('"').strip("'")
EK=ENV['ETHERSCAN_API_KEY']
CACHE=os.path.join(os.path.dirname(__file__),'cache'); os.makedirs(CACHE,exist_ok=True)
_last=[0]
def http(url, data=None, headers=None, cache=True, tries=5, min_gap=0.0):
    key=hashlib.sha1((url+json.dumps(data or '')).encode()).hexdigest()
    fp=os.path.join(CACHE,key+'.json')
    if cache and os.path.exists(fp): return json.load(open(fp))
    h={'User-Agent':'Mozilla/5.0','Accept':'application/json'}; h.update(headers or {})
    body=None
    if data is not None: body=json.dumps(data).encode(); h['Content-Type']='application/json'
    err=None
    for i in range(tries):
        gap=time.time()-_last[0]
        if gap<min_gap: time.sleep(min_gap-gap)
        _last[0]=time.time()
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,data=body,headers=h),timeout=60)
            out=json.loads(r.read())
            if cache: json.dump(out,open(fp,'w'))
            return out
        except urllib.error.HTTPError as e:
            err=f'HTTP {e.code} {e.read()[:200]}'
            if e.code in (400,404): break
        except Exception as e:
            err=repr(e)
        time.sleep(1.5*(i+1))
    raise RuntimeError(f'FAIL {url[:160]} :: {err}')

def es(chainid, **params):
    """Etherscan V2. Loud on error; returns list result or raises."""
    params.update(chainid=chainid, apikey=EK)
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for i in range(6):
        d=http(url, cache=False, min_gap=0.35)
        msg=str(d.get('message','')); res=d.get('result')
        if d.get('status')=='1': 
            return res
        if 'No transactions found' in msg or 'No records found' in msg or (isinstance(res,list) and res==[] and msg.startswith('No')):
            return []
        if 'rate limit' in str(res).lower() or 'Max calls' in str(res):
            time.sleep(2); continue
        if params.get('action')=='eth_getTransactionReceipt' or 'jsonrpc' in d:
            return d
        raise RuntimeError(f'ES error chain={chainid} {params.get("action")} {msg} {str(res)[:200]}')
    raise RuntimeError('ES rate-limited repeatedly')

def es_all(chainid, action, address, **kw):
    """paginate by block to beat 10k cap"""
    out=[]; start=0
    while True:
        r=es(chainid, module='account', action=action, address=address, startblock=start, endblock=99999999, sort='asc', page=1, offset=10000, **kw)
        out+=r
        if len(r)<10000: break
        start=int(r[-1]['blockNumber'])
        # drop duplicates of last block
        out=[x for x in out if int(x['blockNumber'])<start]
    seen=set(); ded=[]
    for x in out:
        k=(x['hash'],x.get('logIndex'),x.get('traceId'),x.get('contractAddress'),x.get('value'),x.get('from'),x.get('to'))
        if k in seen: continue
        seen.add(k); ded.append(x)
    return ded

def pm_activity(user):
    """data-api activity, ASC with timestamp windows (offset cap 5000)."""
    out=[]; start=0; seen=set()
    while True:
        url=f'https://data-api.polymarket.com/activity?user={user}&limit=500&sortBy=TIMESTAMP&sortDirection=ASC&start={start}'
        off=0; page_rows=[]
        while True:
            d=http(url+f'&offset={off}', cache=False, min_gap=0.2)
            if not isinstance(d,list): raise RuntimeError(f'pm activity non-list {str(d)[:200]}')
            page_rows+=d
            if len(d)<500 or off>=4500: break
            off+=500
        new=0
        for x in page_rows:
            k=(x.get('transactionHash'),x.get('type'),x.get('asset'),x.get('size'),x.get('side'),x.get('timestamp'),x.get('usdcSize'))
            if k in seen: continue
            seen.add(k); out.append(x); new+=1
        if len(page_rows)<5000 or new==0: break
        start=max(int(x['timestamp']) for x in page_rows)
    return out

def relay_req(txhash):
    return http(f'https://api.relay.link/requests/v2?hash={txhash}', cache=True, min_gap=0.3)
