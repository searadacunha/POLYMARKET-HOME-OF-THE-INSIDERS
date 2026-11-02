import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
net.RPC[56]=('https://bsc-rpc.publicnode.com','https://bsc-dataseed.bnbchain.org','https://bsc.drpc.org','https://1rpc.io/bnb')
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
out=dict(bsc={},solana={})
ST=json.loads(Path('evidence/thin_step4.json').read_text())
# 1. BSC deposits named by Relay's record.
for h in ('0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2','0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1'):
    rc=net.rpc('eth_getTransactionReceipt',[h],56)
    ts=net.block_time(int(rc['blockNumber'],16),56)
    logs=[dict(log=int(l['logIndex'],16),token=l['address'].lower(),src='0x'+l['topics'][1][-40:],dst='0x'+l['topics'][2][-40:],raw=str(int(l['data'],16))) for l in rc['logs'] if l['topics'] and l['topics'][0]==net.TRANSFER and len(l['topics'])==3]
    out['bsc'][h]=dict(status=rc['status'],sender=rc['from'],to=rc['to'],at=ts,utc=U(ts),logs=logs)
    print('BSC',h[:14],rc['status'],'from',rc['from'],'to',rc['to'],U(ts),json.dumps(logs)[:800])
# 2. Solana: read the payouts directly, then the histories, checked against those payouts.
KNOWN=ST['solana']
rec1=ST['deposits']['dep1']['relay'][0]
print('dep1 in',rec1['in_txs'],rec1['user'],rec1.get('cin'),rec1.get('ain'))
origin_sig=rec1['in_txs'][0][1]
for addr,must in [(a,v['payouts']) for a,v in KNOWN.items()]+[(rec1['user'],[origin_sig])]:
    sigs,complete=sol.signatures(addr,limit=500,max_pages=2,must_contain=must)
    print('SOL',addr,'sigs',len(sigs),'complete',complete,'first',U(sigs[-1]['blockTime']) if sigs else None,'last',U(sigs[0]['blockTime']) if sigs else None)
    rows=[]
    chosen=sigs if len(sigs)<=60 else sigs[-30:]+sigs[:30]
    for s in reversed(chosen):
        tx=sol.transaction(s['signature'])
        mv=sol.token_moves(tx); nat=sol.native_moves(tx)
        prog=sorted({(i.get('program') or i.get('programId','')[:10]) for i in tx['transaction']['message']['instructions']})
        rows.append(dict(sig=s['signature'],at=s['blockTime'],err=s.get('err'),moves=mv,native=nat,programs=prog))
        mine=[m for m in mv if m['owner']==addr]; mynat=[n for n in nat if n['owner']==addr]
        print(' ',U(s['blockTime']),s['signature'][:12],'ERR' if s.get('err') else '','mine',[(m['mint'][:5],round(m['delta'],3)) for m in mine],[('SOL',round(n['delta'],3)) for n in mynat],'others',[(str(m['owner'])[:9],m['mint'][:5],round(m['delta'],2)) for m in mv if m['owner']!=addr][:3],'nat',[(n['owner'][:9],round(n['delta'],2)) for n in nat if n['owner']!=addr][:2],prog[:3])
    out['solana'][addr]=dict(signatures=len(sigs),complete=complete,shown=len(chosen),rows=rows)
    Path('evidence/thin_step5.json').write_text(json.dumps(out,indent=1))
print('calls',net.Stats.calls)
