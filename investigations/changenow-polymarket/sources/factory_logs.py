#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
from eth_hash.auto import keccak
from eth_utils import to_checksum_address
from proxy_resolver import resolve
cfg={l.split('=',1)[0].strip():l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']
def es(p):
    p=dict(p);p['chainid']=137;p['apikey']=KEY
    return json.loads(urllib.request.urlopen("https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p),timeout=40).read())
FACT="0x00000000000fb5c9adea0298d729a0cb3823cc07"
topic0="0x"+keccak(b"WalletDeployed(address,address,bytes32,address)").hex()
print("topic0 WalletDeployed:",topic0)
# get logs (latest block first via a wide range using 'logs' getLogs)
r=es({'module':'logs','action':'getLogs','address':FACT,'topic0':topic0,'page':1,'offset':20})
res=r.get('result',[])
print("n logs fetched:",len(res) if isinstance(res,list) else res)
if isinstance(res,list):
    LEGACY_IMPL="0x58ca52ebe0dadfdf531cde7062e76746de4db1eb"
    shapes={}; matches=0; n=0
    for lg in res[:20]:
        topics=lg['topics']; data=lg['data'][2:]
        # topics = [sig, wallet(indexed), owner(indexed), id(indexed)], data = impl
        wallet=to_checksum_address("0x"+topics[1][26:])
        owner=to_checksum_address("0x"+topics[2][26:])
        impl=to_checksum_address("0x"+data[24:64]) if len(data)>=64 else "0x?"
        shape="LEGACY" if impl.lower()==LEGACY_IMPL else f"OTHER({impl[:10]})"
        pred=resolve(owner)
        ok=pred.lower()==wallet.lower()
        matches+=ok; n+=1
        shapes[shape]=shapes.get(shape,0)+1
        print(f"  owner={owner} wallet={wallet} impl={impl[:10]} {shape} match={ok}")
    print(f"\nresolver matches: {matches}/{n}")
    print("shape counts:",shapes)
