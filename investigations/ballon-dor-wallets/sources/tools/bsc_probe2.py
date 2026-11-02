import json,urllib.request,urllib.error
DEP='0x8e43af995577339436e071990e524ebfe6c09865'; T='0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'
TR='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; PAD='0x'+DEP[2:].rjust(64,'0')
HS='0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2'
def call(u,m,p):
    r=urllib.request.Request(u,data=json.dumps(dict(jsonrpc='2.0',id=1,method=m,params=p)).encode(),headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(r,timeout=25) as f: return json.loads(f.read())
    except urllib.error.HTTPError as e:
        return dict(error=f'HTTP {e.code} '+e.read()[:140].decode(errors='ignore'))
    except Exception as e: return dict(error=type(e).__name__)
rec=None
for u in ('https://bsc-rpc.publicnode.com','https://bsc-dataseed.bnbchain.org'):
    x=call(u,'eth_getTransactionReceipt',[HS])
    if x.get('result'): rec=x['result'];break
b=int(rec['blockNumber'],16); print('block',b)
for u in ('https://bsc-rpc.publicnode.com','https://bsc.drpc.org','https://1rpc.io/bnb','https://bsc.blockrazor.xyz','https://rpc-bsc.48.club','https://bsc.publicnode.com','https://bscrpc.com','https://bsc.blockpi.network/v1/rpc/public','https://bnb.rpc.subquery.network/public','https://api.zan.top/bsc-mainnet','https://bsc.rpc.blxrbdn.com','https://bsc-mainnet.gateway.tatum.io','https://rpc.ankr.com/bsc','https://bnb.rpc.hypersync.xyz','https://bsc.therpc.io','https://bsc.nownodes.io','https://koge-rpc-bsc.48.club','https://bsc.rpc.thirdweb.com','https://56.rpc.thirdweb.com'):
    for span in (0,24):
        r=call(u,'eth_getLogs',[dict(address=T,fromBlock=hex(b-span),toBlock=hex(b),topics=[TR,PAD])])
        print(u,'span',span,('LOGS '+str(len(r['result']))) if 'result' in r else str(r.get('error'))[:150])
        if 'result' not in r: break
