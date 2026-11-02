import json,sys
from pathlib import Path
sys.path.insert(0,'tools')
import net
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com')
d=json.load(open('graphs/links.json'))
A={137:[net.TOKENS['USDC.e'],net.TOKENS['USDC'],net.TOKENS['USDT']],1:['0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7'],42161:['0xaf88d065e77c8cc2239327c5edb3a432268e5831']}
out=[]
seen=set()
for x in d['shared_non_infrastructure']:
    a=x['address']
    if not a.startswith('0x') or a in seen: continue
    seen.add(a)
    row=dict(address=a,cases=x['cases'],chains={})
    for ch in x['chains']:
        if ch not in A: continue
        code=net.rpc('eth_getCode',[a,'latest'],ch); n=net.nonce(a,ch)
        head=int(net.rpc('eth_blockNumber',[],ch),16); w=9000 if ch==137 else 3000
        o=net.rpc('eth_getLogs',[dict(address=A[ch],fromBlock=hex(head-w),toBlock=hex(head),topics=[net.TRANSFER,net.pad(a)])],ch)
        span=net.block_time(head,ch)-net.block_time(head-w,ch)
        row['chains'][ch]=dict(kind='EOA' if code=='0x' else '7702' if code.startswith('0xef0100') else 'CONTRACT',nonce=n,sample_hours=round(span/3600,1),outflows=len(o),receivers=len({l['topics'][2] for l in o}))
    out.append(row);print(row)
Path('evidence/shared_kinds.json').write_text(json.dumps(out,indent=1))
