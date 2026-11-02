import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net
net.RPC[56]=('https://bsc.drpc.org','https://bsc-dataseed.bnbchain.org','https://1rpc.io/bnb','https://bsc-rpc.publicnode.com')
THIN='0x8d3319c51520518ad01f6744486ceea29f376f5b'; DEP='0x8e43af995577339436e071990e524ebfe6c09865'; OWNER='0x1bf0b469f7f3612657e99bf785e470eee2a76028'
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
out={}
def logs_of(rc,chain):
    res=[]
    for l in rc['logs']:
        if l['topics'] and l['topics'][0]==net.TRANSFER and len(l['topics'])==3:
            res.append(dict(log=int(l['logIndex'],16),token=l['address'].lower(),src='0x'+l['topics'][1][-40:],dst='0x'+l['topics'][2][-40:],raw=int(l['data'],16) if l['data']!='0x' else 0))
    return res
for name,h in (('bsc_11946','0xce687a68b2211502da1c4056978b3224d2c3492ee60405ec7fd1bfa142fdff18'),('bsc_21900','0x81ea0ed6d74dd68b002c1de7d1ecd5550bd8285aeb5032bb249848b3a3578f40')):
    try:
        rc=net.rpc('eth_getTransactionReceipt',[h],56)
        tx=net.rpc('eth_getTransactionByHash',[h],56)
        block=int(rc['blockNumber'],16); ts=net.block_time(block,56)
        out[name]=dict(hash=h,status=rc['status'],sender=rc['from'],to=rc['to'],block=block,at=ts,utc=U(ts),input_head=tx['input'][:10],logs=logs_of(rc,56))
        print(name,rc['status'],rc['from'],'->',rc['to'],U(ts),json.dumps(out[name]['logs'])[:900])
    except Exception as e:
        out[name]=dict(hash=h,error=str(e)[:200]); print(name,'ERR',str(e)[:300])
for name,h in (('pol_a','0xca47dd68fc8d2a34a27c93610933cca0cfd0f71bfaead25f60a918c9ea3b7325'),('pol_b','0x848da5b598772a13cf4215af2d54316219e3b6099caf55382298babb9af9a7ce'),('pol_c','0x99b1360079ed4cf47302dacdd0ddae8b9c6556e26d5073649e990c38cc30f045'),('dep1','0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1'),('dep2','0x1e2c6576867d250de440e43b97bc01fd456952c30b1c6811fa0665cbf216a2f6'),('dep3','0x975d526512ae2b0af5dc50b05af0b409b8686dfe9a522409483342bccc084aec')):
    try:
        rc=net.rpc('eth_getTransactionReceipt',[h],137)
        ts=net.block_time(int(rc['blockNumber'],16))
        L=[x for x in logs_of(rc,137) if DEP in (x['src'],x['dst']) or THIN in (x['src'],x['dst']) or x['raw'] in (11833228666,11946000000,21900004500)]
        out[name]=dict(hash=h,status=rc['status'],sender=rc['from'],to=rc['to'],block=int(rc['blockNumber'],16),at=ts,utc=U(ts),n_logs=len(rc['logs']),logs=L)
        print(name,rc['status'],rc['from'],'->',rc['to'],U(ts),'nlogs',len(rc['logs']),json.dumps(L)[:1100])
    except Exception as e:
        out[name]=dict(hash=h,error=str(e)[:200]); print(name,'ERR',str(e)[:300])
print('code at DEP',net.rpc('eth_getCode',[DEP,'latest'])[:200])
for ch,nm in ((1,'eth'),(56,'bsc'),(42161,'arb'),(8453,'base'),(10,'op'),(137,'pol')):
    try: print('owner nonce',nm,net.nonce(OWNER,ch),'code',net.is_contract(OWNER,ch))
    except Exception as e: print('owner',nm,'ERR',str(e)[:120])
for q in ({'id':'0x3d7a25fd74a90812f985ba098bcca980da4040974ceb6b303d8078e1ba524515'},{'hash':'0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e'},{'user':THIN},{'user':OWNER}):
    r=net.get('https://api.relay.link/requests/v2',q)
    print('relay',q,json.dumps(r)[:1500])
Path('evidence/thin_step2.json').write_text(json.dumps(out,indent=1))
print('calls',net.Stats.calls)
