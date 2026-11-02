#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
cfg = {l.split('=',1)[0].strip(): l.split('=',1)[1].strip()
       for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY = cfg['ETHERSCAN_API_KEY']
def es(p):
    p = dict(p); p['chainid']=137; p['apikey']=KEY
    return json.loads(urllib.request.urlopen("https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p),timeout=40).read())
tx = "0x21d931a5dd9469fe46a33ec94667a6514a82d8fc0f1e71497d8f5c7445e83bd4"
r = es({'module':'proxy','action':'eth_getTransactionByHash','txhash':tx})
res = r.get('result',{})
print("FROM:", res.get('from'))
print("TO  :", res.get('to'))
inp = res.get('input','')
print("INPUT len:", len(inp))
print("INPUT:", inp)
