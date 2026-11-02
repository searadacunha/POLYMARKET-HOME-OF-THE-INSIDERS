import json,sys,time,collections
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t)) if t else None
out={}
MINT={'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':'USDC','Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB':'USDT','So11111111111111111111111111111111111111112':'WSOL'}
# 1. Gxjc: who pays it, who it pays, in the last 300 signatures, and around the two deposits.
G='GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
sigs=sol.rpc('getSignaturesForAddress',[G,dict(limit=300)])
inn,oot=collections.Counter(),collections.Counter(); ins,outs=[],[]; sample=[]
for s in sigs[:120]:
    t=sol.transaction(s['signature'])
    mv=sol.token_moves(t); nat=sol.native_moves(t,.05)
    me=[m for m in mv if m['owner']==G]; others=[m for m in mv if m['owner']!=G]
    my=[n for n in nat if n['owner']==G]
    for m in me:
        (ins if m['delta']>0 else outs).append((MINT.get(m['mint'],m['mint'][:6]),round(m['delta'],2)))
    for m in others:
        (inn if m['delta']<0 else oot)[m['owner']]+=1
    for n in nat:
        if n['owner']!=G: (inn if n['delta']<0 else oot)[n['owner']]+=1
    sample.append(dict(sig=s['signature'],at=s['blockTime'],me=me,others=others[:4],nat=nat[:3]))
print('Gxjc sample 120 txs',U(sigs[119]['blockTime']),U(sigs[0]['blockTime']),'token in',len(ins),'token out',len(outs),'distinct payers',len(inn),'distinct receivers',len(oot))
print(' token in sample',ins[:14]);print(' token out sample',outs[:14]);print(' top payers',inn.most_common(5));print(' top receivers',oot.most_common(6))
out['gxjc']=dict(sample=len(sample),ins=ins,outs=outs,payers=inn.most_common(40),receivers=oot.most_common(40))
# 2. 0xee7a: sample recent USDC traffic per chain.
E='0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055'
for ch,toks,width in ((137,[net.TOKENS['USDC.e'],net.TOKENS['USDC']],3000),(42161,['0xaf88d065e77c8cc2239327c5edb3a432268e5831'],9000),(1,['0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'],1000),(8453,['0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'],3000)):
    head=int(net.rpc('eth_blockNumber',[],ch),16)
    try:
        o=net.rpc('eth_getLogs',[dict(address=toks,fromBlock=hex(head-width),toBlock=hex(head),topics=[net.TRANSFER,net.pad(E)])],ch)
        i=net.rpc('eth_getLogs',[dict(address=toks,fromBlock=hex(head-width),toBlock=hex(head),topics=[net.TRANSFER,None,net.pad(E)])],ch)
        span=net.block_time(head,ch)-net.block_time(head-width,ch)
        print('0xee7a chain',ch,'recent window',round(span/3600,2),'h outflows',len(o),'inflows',len(i),'distinct out',len({l['topics'][2] for l in o}),'distinct in',len({l['topics'][1] for l in i}))
        out.setdefault('ee7a',{})[ch]=dict(hours=span/3600,out=len(o),inn=len(i))
    except Exception as e: print('0xee7a',ch,'ERR',str(e)[:120])
impl=None
try:
    net.READ_METHODS=net.READ_METHODS|{'eth_getStorageAt'}
    impl=net.rpc('eth_getStorageAt',[E,'0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc','latest'],137)
    print('0xee7a implementation',impl)
except Exception as e: print('impl ERR',str(e)[:120])
for sel,nm in (('0xa0e67e2b','getOwners'),('0x8da5cb5b','owner'),('0xe75235b8','getThreshold')):
    try: print(' ',nm,net.rpc('eth_call',[dict(to=E,data=sel),'latest'],137)[:200])
    except Exception as e: print(' ',nm,'ERR',str(e)[:80])
# 3. 0xc8a6: distinct wallets in a recent window.
C='0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'
head=int(net.rpc('eth_blockNumber',[],137),16)
o=net.rpc('eth_getLogs',[dict(address=[net.TOKENS['USDC.e'],net.TOKENS['pUSD']],fromBlock=hex(head-9000),toBlock=hex(head),topics=[net.TRANSFER,net.pad(C)])],137)
i=net.rpc('eth_getLogs',[dict(address=[net.TOKENS['USDC.e'],net.TOKENS['USDC']],fromBlock=hex(head-9000),toBlock=hex(head),topics=[net.TRANSFER,None,net.pad(C)])],137)
span=net.block_time(head)-net.block_time(head-9000)
print('0xc8a6 window',round(span/3600,2),'h out',len(o),'in',len(i),'tx',len({l['transactionHash'] for l in o}),'distinct payers',len({l['topics'][1] for l in i}))
out['c8a6']=dict(hours=span/3600,out=len(o),inn=len(i),payers=len({l['topics'][1] for l in i}))
Path('evidence/hubs.json').write_text(json.dumps(out,indent=1))
print('calls',net.Stats.calls)
