"""Any direct transfer between the addresses of the eleven cases, on Polygon and Ethereum, stablecoins and pUSD, and position tokens on Polygon, from 25 Sept to now. One OR-filter per chunk, so this stays light."""
import glob,json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,identities as I
S={}
for s in I.IDS:
    c=json.load(open(f'cases/{s}.json'))
    S[c['address'].lower()]=(s,'wallet')
    for o in (c.get('wallet') or {}).get('owners') or []: S[o.lower()]=(s,'owner')
    for h in c.get('funding_chain',[]):
        if h and h.get('immediate_source') and h['kind']['kind']!='CONTRACT': S.setdefault(h['immediate_source'].lower(),(s,'bridge_address'))
    for x in c.get('recipients',[]):
        if str(x['address']).startswith('0x'): S.setdefault(x['address'].lower(),(s,'recipient'))
    for f in c.get('exit_follow',[]):
        for k in f.get('hops',[]):
            if not k.get('label') and k['kind']['kind']=='EOA' and k['kind']['nonce']<1000: S.setdefault(k['target'].lower(),(s,'next_hop'))
print('addresses',len(S),{t:sum(1 for v in S.values() if v[1]==t) for t in('wallet','owner','bridge_address','recipient','next_hop')})
P=[net.pad(a) for a in S]
TS='0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62'
BATCH='0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb'
CT='0x4d97dcd97ec945f40cf65f87097ace5ea0476045'
out=dict(addresses=len(S),hits=[],chunks={},read_at=time.time())
def block_at(chain,m):
    lo,hi=1,int(net.rpc('eth_blockNumber',[],chain),16)
    for _ in range(45):
        if hi-lo<=1: break
        mid=(lo+hi)//2
        if net.block_time(mid,chain)<m: lo=mid
        else: hi=mid
    return hi
START=1790294400
for chain,addr,step in ((137,[net.TOKENS['USDC.e'],net.TOKENS['USDC'],net.TOKENS['pUSD'],net.TOKENS['USDT']],9000),(1,['0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7'],5000)):
    lo,hi=block_at(chain,START),int(net.rpc('eth_blockNumber',[],chain),16)
    n=0
    for s in range(lo,hi+1,step):
        for l in net.rpc('eth_getLogs',[dict(address=addr,fromBlock=hex(s),toBlock=hex(min(hi,s+step-1)),topics=[net.TRANSFER,P,P])],chain):
            a,b='0x'+l['topics'][1][-40:],'0x'+l['topics'][2][-40:]
            out['hits'].append(dict(chain=chain,kind='erc20',token=l['address'].lower(),source=a,source_case=S[a],target=b,target_case=S[b],tx=l['transactionHash'],log=int(l['logIndex'],16),raw=str(int(l['data'],16)),at=net.block_time(int(l['blockNumber'],16),chain)))
        n+=1
    out['chunks'][chain]=dict(blocks=[lo,hi],chunks=n)
    print('chain',chain,'chunks',n,'hits so far',len(out['hits']),flush=True)
# Position tokens: operator is free, from and to must both be in the set.
lo,hi=block_at(137,START),int(net.rpc('eth_blockNumber',[],137),16)
for s in range(lo,hi+1,9000):
    for topic in (TS,BATCH):
        for l in net.rpc('eth_getLogs',[dict(address=CT,fromBlock=hex(s),toBlock=hex(min(hi,s+8999)),topics=[topic,None,P,P])],137):
            a,b='0x'+l['topics'][2][-40:],'0x'+l['topics'][3][-40:]
            out['hits'].append(dict(chain=137,kind='position',source=a,source_case=S[a],target=b,target_case=S[b],tx=l['transactionHash'],log=int(l['logIndex'],16),at=net.block_time(int(l['blockNumber'],16))))
print('positions done, hits',len(out['hits']),flush=True)
Path('graphs/direct_transfers.json').write_text(json.dumps(out,indent=1))
cross=[h for h in out['hits'] if h['source_case'][0]!=h['target_case'][0]]
print('within one case',len(out['hits'])-len(cross),'across cases',len(cross))
for h in cross[:30]: print(h['source_case'],'->',h['target_case'],h['chain'],h['kind'],h.get('raw'),h['tx'])
print('calls',net.Stats.calls)
