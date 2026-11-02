"""Phase 7 : vérification reproductible (1) des enregistrements ENS moonpay.eth / ivanhodl.eth,
(2) de la chaîne de propriété du nom moonpay.eth, (3) des transferts entre MoonPay 7, moonpay.eth,
ivanhodl.eth, l'admin 0xf691384d et la famille. Sources : Etherscan API (eth_call, getLogs, txlist)."""
import json,datetime as dt
from eth_hash.auto import keccak
from common2 import es
from deep_evm import pull
REG='0x00000000000c2e074ec69a0dfb2997ba6c7d2e1e'; BASE='0x57f1887a8bf19b14fc0df6fd9b2acc9af147ea85'
def namehash(name):
    node=b'\x00'*32
    for label in reversed(name.split('.')): node=keccak(node+keccak(label.encode()))
    return node
def sel(sig): return keccak(sig.encode())[:4].hex()
def call(to,data):
    r=es(1,module='proxy',action='eth_call',to=to,data=data,tag='latest'); return r.get('result') if isinstance(r,dict) else r
out={}
for name in ('moonpay.eth','ivanhodl.eth'):
    n=namehash(name).hex(); res='0x'+call(REG,'0x'+sel('resolver(bytes32)')+n)[-40:]
    out[name]={'registry_owner':'0x'+call(REG,'0x'+sel('owner(bytes32)')+n)[-40:],'resolver':res,'addr':'0x'+call(res,'0x'+sel('addr(bytes32)')+n)[-40:]}
for a in ('d75233704795206de38cc58b77a1f660b5c60896','695626a661831a618ae846482fe8abf6c8d4529c'):
    n=namehash(a+'.addr.reverse').hex(); res='0x'+call(REG,'0x'+sel('resolver(bytes32)')+n)[-40:]
    b=bytes.fromhex(call(res,'0x'+sel('name(bytes32)')+n)[2:]); ln=int.from_bytes(b[32:64],'big'); out['reverse_0x'+a]=b[64:64+ln].decode()
lh='0x'+keccak(b'moonpay').hex(); t0='0x'+keccak(b'Transfer(address,address,uint256)').hex()
out['moonpay.eth_nft_transfers']=[(dt.datetime.fromtimestamp(int(l['timeStamp'],16),dt.UTC).isoformat(),'0x'+l['topics'][1][-40:],'0x'+l['topics'][2][-40:],l['transactionHash']) for l in (es(1,module='logs',action='getLogs',address=BASE,topic0=t0,topic3=lh,topic0_3_opr='and',fromBlock=0,toBlock='latest') or [])]
json.dump(out,open('p7_ens.json','w'),indent=1); print(json.dumps(out,indent=1))
