import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com')
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
DEP='0x8e43af995577339436e071990e524ebfe6c09865'; T='0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'
out=dict(positive_control={},bsc_in={},origin={})
def find_block(chain,moment):
    lo,hi=1,int(net.rpc('eth_blockNumber',[],chain),16)
    for _ in range(45):
        if hi-lo<=1: break
        mid=(lo+hi)//2
        if net.block_time(mid,chain)<moment: lo=mid
        else: hi=mid
    return hi
# Positive control: the known outflow must come back from the same kind of filter, or a zero below means nothing.
for name,h in (('dep2','0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2'),('dep3','0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1')):
    b=int(net.rpc('eth_getTransactionReceipt',[h],56)['blockNumber'],16)
    logs=net.rpc('eth_getLogs',[dict(address=T,fromBlock=hex(b),toBlock=hex(b),topics=[net.TRANSFER,net.pad(DEP)])],56)
    out['positive_control'][name]=len(logs); assert logs, 'node misses a known log: its zeros are not usable'
print('positive control',out['positive_control'])
# Every inflow of this token to the bridge address, from a week before the first BSC deposit to the last.
for name,moment,back in (('dep2',1791899226,3600),('dep3',1791916615,3600)):
    hi=find_block(56,moment+5); lo=find_block(56,moment-back)
    rows=[]
    for s in range(lo,hi+1,100):
        rows+=net.rpc('eth_getLogs',[dict(address=T,fromBlock=hex(s),toBlock=hex(min(hi,s+99)),topics=[net.TRANSFER,None,net.pad(DEP)])],56)
    res=[dict(tx=l['transactionHash'],log=int(l['logIndex'],16),block=int(l['blockNumber'],16),at=net.block_time(int(l['blockNumber'],16),56),src='0x'+l['topics'][1][-40:],raw=str(int(l['data'],16))) for l in rows]
    out['bsc_in'][name]=dict(blocks=[lo,hi],rows=res)
    print('BSC in',name,lo,hi,hi-lo,[(U(r['at']),r['src'],int(r['raw'])/1e18,r['tx']) for r in res])
    Path('evidence/thin_step7.json').write_text(json.dumps(out,indent=1))
seen=set()
for name,v in out['bsc_in'].items():
    for r in v['rows']:
        if r['tx'] in seen: continue
        seen.add(r['tx'])
        rc=net.rpc('eth_getTransactionReceipt',[r['tx']],56)
        tx=net.rpc('eth_getTransactionByHash',[r['tx']],56)
        src=r['src']
        info=dict(tx=r['tx'],sender=rc['from'],to=rc['to'],n_logs=len(rc['logs']),src=src,src_code=net.rpc('eth_getCode',[src,'latest'],56)[:24],src_nonce=net.nonce(src,56),src_bnb=int(net.rpc('eth_getBalance',[src,'latest'],56),16)/1e18,sender_nonce=net.nonce(rc['from'],56))
        out['origin'][r['tx']]=info; print('ORIGIN',json.dumps(info))
Path('evidence/thin_step7.json').write_text(json.dumps(out,indent=1)); print('calls',net.Stats.calls)
