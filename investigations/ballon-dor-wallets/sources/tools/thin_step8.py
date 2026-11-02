"""Finds the block where the bridge address received BSC USDC by bisecting its balance, then reads that one block's logs. A dozen calls instead of scanning every block."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com','https://bsc.blockrazor.xyz')
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
DEP='0x8e43af995577339436e071990e524ebfe6c09865'; T='0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'
def bal(block):
    time.sleep(1.5)
    return int(net.rpc('eth_call',[dict(to=T,data='0x70a08231'+DEP[2:].rjust(64,'0')),hex(block)],56),16)
out=json.loads(Path('evidence/thin_step7.json').read_text()) if Path('evidence/thin_step7.json').exists() else {}
out['bisect']={}
for name,h,amount in (('dep2','0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2',11946*10**18),('dep3','0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1',21900004500*10**12)):
    spend=int(net.rpc('eth_getTransactionReceipt',[h],56)['blockNumber'],16)
    hi=spend-1
    # The balance before the bridge spends it. Earlier blocks may lack it: walk back until it is below the amount.
    if bal(hi)<amount:
        hi=spend  # funded within the spending block itself
    step=2000; lo=hi-step
    while bal(lo)>=amount:
        step*=2; lo=hi-step
    while hi-lo>1:
        mid=(lo+hi)//2
        if bal(mid)>=amount: hi=mid
        else: lo=mid
    time.sleep(2)
    logs=net.rpc('eth_getLogs',[dict(address=T,fromBlock=hex(hi),toBlock=hex(hi),topics=[net.TRANSFER,None,net.pad(DEP)])],56)
    res=[]
    for l in logs:
        tx=l['transactionHash']; time.sleep(1.5)
        rc=net.rpc('eth_getTransactionReceipt',[tx],56); time.sleep(1.5)
        src='0x'+l['topics'][1][-40:]
        res.append(dict(tx=tx,log=int(l['logIndex'],16),block=hi,at=net.block_time(hi,56),source=src,raw=str(int(l['data'],16)),submitter=rc['from'],to=rc['to'],n_logs=len(rc['logs']),source_code=net.rpc('eth_getCode',[src,'latest'],56)[:26],source_nonce=net.nonce(src,56)))
    out['bisect'][name]=dict(spend_block=spend,funded_block=hi,rows=res)
    Path('evidence/thin_step7.json').write_text(json.dumps(out,indent=1))
    print(name,'funded block',hi,[(U(r['at']),r['source'],int(r['raw'])/1e18,r['tx'],'submitter',r['submitter'],'nonce',r['source_nonce'],r['source_code']) for r in res])
print('calls',net.Stats.calls)
