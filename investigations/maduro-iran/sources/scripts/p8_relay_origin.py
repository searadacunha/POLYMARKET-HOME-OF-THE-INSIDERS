"""Phase 8 : origine des afflux Relay (solveur 0xf70da978) vers les proxys Polygon : Relay API (hash) -> adresse d'origine,
puis paiements de la famille / wallets MoonPay vers cette adresse d'origine (Etherscan, chaîne d'origine). Horodatage conservé."""
import json,os,sys
from common2 import http,es
from p8_sets import MOON
RELAY='0xf70da97812cb96acdf810712aa562db8dfa3dbef'
wallets=json.load(open(sys.argv[1])); K,N=(int(sys.argv[2]),int(sys.argv[3])) if len(sys.argv)>3 else (0,1)
os.makedirs('p8/relayorig',exist_ok=True)
def origin_funding(addr,chain):
    fp=f'p8/relayorig/o_{chain}_{addr}.json'
    if os.path.exists(fp): return json.load(open(fp))
    out=[]
    for act in ('tokentx','txlist'):
        try: r=es(chain,module='account',action=act,address=addr,page=1,offset=1000,sort='asc') or []
        except Exception: r=[]
        for x in r:
            if x['to'].lower()==addr and x['from'].lower() in MOON and int(x['value'])>0: out.append((int(x['timeStamp']),x['from'].lower(),x['hash']))
    json.dump(out,open(fp,'w')); return out
for i,w in enumerate(wallets):
    if i%N!=K: continue
    fp=f'p8/relayorig/{w}.json'
    if os.path.exists(fp) or not os.path.exists(f'p8/funding/{w}.json'): continue
    f=json.load(open(f'p8/funding/{w}.json')); res=[]
    for x in [x for x in f['inflows'] if x[1]==RELAY][:5]:
        try:
            d=http(f'https://api.relay.link/requests/v2?hash={x[4]}',cache=True); q=(d.get('requests') or [None])[0]
        except Exception: q=None
        if not q: res.append(dict(ts=x[0],hash=x[4],origin=None)); continue
        m=q['data'].get('metadata',{}); ch=m.get('currencyIn',{}).get('currency',{}).get('chainId'); u=(q.get('user') or '').lower()
        fam=origin_funding(u,ch) if (u.startswith('0x') and ch in (1,8453,42161,10,137,56)) else []
        res.append(dict(ts=x[0],hash=x[4],origin=u,chain=ch,family=[y for y in fam if y[0]<=x[0]]))
    json.dump(res,open(fp,'w'))
print('done',K)
