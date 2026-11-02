import json,urllib.request,sys
DEP='0x8e43af995577339436e071990e524ebfe6c09865'; T='0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'
TR='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; PAD='0x'+DEP[2:].rjust(64,'0')
def call(u,m,p):
    r=urllib.request.Request(u,data=json.dumps(dict(jsonrpc='2.0',id=1,method=m,params=p)).encode(),headers={'Content-Type':'application/json','User-Agent':'investigation-read-only'})
    with urllib.request.urlopen(r,timeout=20) as f: return json.loads(f.read())
for u in ('https://bsc-mainnet.public.blastapi.io','https://bsc.meowrpc.com','https://binance.llamarpc.com','https://bsc.api.onfinality.io/public','https://bsc.blockrazor.xyz','https://public.stackup.sh/api/v1/node/bsc-mainnet','https://bnb.api.pocket.network','https://bsc-pokt.nodies.app','https://bsc-rpc.publicnode.com','https://rpc-bsc.48.club','https://endpoints.omniatech.io/v1/bsc/mainnet/public'):
    try:
        head=int(call(u,'eth_blockNumber',[])['result'],16)
        # Old range, narrow: does this node serve historical logs with a filter?
        r=call(u,'eth_getLogs',[dict(address=T,fromBlock=hex(head-40000000//40),toBlock=hex(head-40000000//40+500),topics=[TR,None,PAD])])
        print(u,'head',head,'logs',('ok '+str(len(r['result']))) if 'result' in r else str(r.get('error'))[:110])
    except Exception as e: print(u,'ERR',type(e).__name__,str(e)[:80])
