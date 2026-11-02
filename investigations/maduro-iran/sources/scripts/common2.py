# thread/process-safe HTTP with per-host shared throttle + disk cache
import os, json, time, hashlib, fcntl, urllib.request, urllib.parse, threading
from urllib.parse import urlparse
import common
ENV=common.ENV; EK=common.EK
BASE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(BASE,'cache'); os.makedirs(CACHE,exist_ok=True)
RL=os.path.join(BASE,'rl'); os.makedirs(RL,exist_ok=True)
RATE={'api.etherscan.io':4.0,'api.trongrid.io':0.85,'api.relay.link':4.0,'data-api.polymarket.com':6.0,'clob.polymarket.com':5.0,'api.goldsky.com':4.0,'api.helius.xyz':5.0}
def throttle(host):
    r=RATE.get(host,5.0); fp=os.path.join(RL,host)
    with open(fp,'a+') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        f.seek(0); s=f.read().strip(); last=float(s) if s else 0.0
        now=time.time(); nxt=max(now,last+1.0/r)
        if nxt>now: time.sleep(nxt-now)
        f.seek(0); f.truncate(); f.write(str(nxt)); f.flush()
        fcntl.flock(f,fcntl.LOCK_UN)
def http(url, data=None, headers=None, cache=True, tries=6):
    key=hashlib.sha1((url+json.dumps(data or '')).encode()).hexdigest()
    fp=os.path.join(CACHE,key+'.json')
    if cache and os.path.exists(fp):
        try: return json.load(open(fp))
        except Exception: pass
    h={'User-Agent':'curl/8.4.0','Accept':'application/json'}; h.update(headers or {})
    body=None
    if data is not None: body=json.dumps(data).encode(); h['Content-Type']='application/json'
    host=urlparse(url).netloc; err=None
    for i in range(tries):
        throttle(host)
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,data=body,headers=h),timeout=60)
            out=json.loads(r.read())
            if cache: 
                tmp=fp+f'.{threading.get_ident()}'; json.dump(out,open(tmp,'w')); os.replace(tmp,fp)
            return out
        except urllib.error.HTTPError as e:
            err=f'HTTP {e.code} {e.read()[:150]}'
            if e.code in (400,404,422): break
            if e.code==429: time.sleep(6); continue
        except Exception as e: err=repr(e)[:150]
        time.sleep(2*(i+1))
    raise RuntimeError(f'FAIL {url[:140]} :: {err}')
def es(chainid, **params):
    params.update(chainid=chainid, apikey=EK)
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(params)
    for i in range(12):
        d=http(url, cache=False)
        msg=str(d.get('message','')); res=d.get('result')
        if d.get('status')=='1': return res
        if 'No transactions found' in msg or 'No records found' in msg: return []
        if isinstance(res,str) and ('rate limit' in res.lower() or 'max calls' in res.lower()): time.sleep(1.5); continue
        if 'timeout' in msg.lower() or 'busy' in msg.lower() or 'unexpected' in msg.lower() or (isinstance(res,str) and ('timeout' in res.lower() or 'busy' in res.lower())): time.sleep(3*(i+1)); continue
        if 'jsonrpc' in d: return d
        if isinstance(res,list) and res==[]: return []
        raise RuntimeError(f'ES error chain={chainid} {params.get("action")} {msg} {str(res)[:150]}')
    raise RuntimeError('ES rate-limited')
def es_cached(chainid, **params):
    """cacheable etherscan (historical windows only)"""
    p=dict(params); p.update(chainid=chainid, apikey=EK)
    url='https://api.etherscan.io/v2/api?'+urllib.parse.urlencode(p)
    key=hashlib.sha1(url.encode()).hexdigest(); fp=os.path.join(CACHE,'es_'+key+'.json')
    if os.path.exists(fp): return json.load(open(fp))
    r=es(chainid, **params); json.dump(r,open(fp,'w')); return r
