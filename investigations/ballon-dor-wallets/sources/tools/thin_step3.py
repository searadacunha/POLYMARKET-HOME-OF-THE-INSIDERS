import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net
net.RPC[56]=('https://bsc.drpc.org','https://bsc-dataseed.bnbchain.org','https://1rpc.io/bnb')
THIN='0x8d3319c51520518ad01f6744486ceea29f376f5b'; DEP='0x8e43af995577339436e071990e524ebfe6c09865'
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
out=dict(relay={},incoming={})
# 1. Relay records by deposit hash: save the raw answer, the route retires on 24 Nov 2026.
for tx in ('0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e','0x5c4d9506a42a1ecb190233847a7baea1f967766873218d042c714fb00bf31b90','0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c','0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989'):
    time.sleep(20)
    r=net.get('https://api.relay.link/requests/v2',dict(hash=tx),pause=2)
    out['relay'][tx]=r
    for q in r.get('requests',[]):
        d=q.get('data',{}); m=d.get('metadata',{})
        print('RELAY',tx[:12],'id',q['id'],q['status'],'user',q.get('user'),'recipient',q.get('recipient'),'in',[(t.get('chainId'),t.get('hash')) for t in d.get('inTxs',[])],'out',[(t.get('chainId'),t.get('hash')) for t in d.get('outTxs',[])],'cur',json.dumps({k:(m.get(k) or {}).get('amountFormatted') if isinstance(m.get(k),dict) else m.get(k) for k in('currencyIn','currencyOut')}), [ (m.get(k) or {}).get('currency',{}).get('symbol') for k in('currencyIn','currencyOut')])
# 2. Who paid the bridge address, on every chain read here. Same EVM address on each chain. Any token, tight window around each record.
def find_block(chain,moment):
    head=int(net.rpc('eth_blockNumber',[],chain),16); t=net.block_time(head,chain)
    lo,hi=1,head
    for _ in range(40):
        if hi-lo<=1: break
        mid=(lo+hi)//2
        if net.block_time(mid,chain)<moment: lo=mid
        else: hi=mid
    return hi
WIN={'dep1':(1791732214-5400,1791732214+300),'dep2':(1791899231-5400,1791899231+300),'dep3':(1791916620-5400,1791916620+300)}
for chain,step in ((137,1000),(56,4000),(1,1000),(42161,8000),(8453,4000),(10,4000)):
    for name,(a,b) in WIN.items():
        try:
            lo,hi=find_block(chain,a),find_block(chain,b)
            rows=[]
            for s in range(lo,hi+1,step):
                rows+=net.rpc('eth_getLogs',[dict(fromBlock=hex(s),toBlock=hex(min(hi,s+step-1)),topics=[net.TRANSFER,None,net.pad(DEP)])],chain)
            res=[dict(chain=chain,tx=l['transactionHash'],log=int(l['logIndex'],16),block=int(l['blockNumber'],16),at=net.block_time(int(l['blockNumber'],16),chain),token=l['address'].lower(),src='0x'+l['topics'][1][-40:],raw=str(int(l['data'],16))) for l in rows if len(l['topics'])==3 and l['data']!='0x']
            out['incoming'][f'{chain}_{name}']=dict(blocks=[lo,hi],rows=res)
            print('IN',chain,name,lo,hi,len(res),[(U(x['at']),x['token'][:10],x['src'],int(x['raw'])/ (1e18 if chain==56 else 1e6),x['tx'][:14]) for x in res][:6])
        except Exception as e:
            out['incoming'][f'{chain}_{name}']=dict(error=str(e)[:300]); print('IN',chain,name,'ERR',str(e)[:200])
Path('evidence/thin_step3.json').write_text(json.dumps(out,indent=1)); print('calls',net.Stats.calls,'cached',net.Stats.cached)
