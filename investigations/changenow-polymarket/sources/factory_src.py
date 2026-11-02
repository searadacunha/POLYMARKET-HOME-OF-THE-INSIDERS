#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
cfg = {l.split('=',1)[0].strip(): l.split('=',1)[1].strip()
       for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY = cfg['ETHERSCAN_API_KEY']
def es(p):
    p=dict(p); p['chainid']=137; p['apikey']=KEY
    return json.loads(urllib.request.urlopen("https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p),timeout=40).read())
FACT="0x00000000000fb5c9adea0298d729a0cb3823cc07"
r=es({'module':'contract','action':'getsourcecode','address':FACT})
res=r['result'][0]
print("ContractName:", res.get('ContractName'))
print("Compiler:", res.get('CompilerVersion'))
src=res.get('SourceCode','')
print("SOURCE len:", len(src))
# find salt/create2 logic
low=src.lower()
for kw in ['create2','salt','keccak','getproxy','computeaddress','maybemakewallet','proxy']:
    i=low.find(kw)
    print(f"  kw {kw!r} at {i}")
# dump the source to a file for reading
open("state/factory_source.txt","w").write(src)
print("-> state/factory_source.txt")
