"""What each EVM recipient of a withdrawal still holds of the token it received. A stablecoin balance only: native coin and other tokens are not read."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,identities as I
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com')
out={}
for s in I.IDS:
    c=json.load(open(f'cases/{s}.json'))
    seen={}
    for h in c.get('exit_chain',[]):
        if not h or not h.get('relay') or not h['relay'].get('out_txs'): continue
        ch,tx=h['relay']['out_txs'][0]
        if ch not in net.RPC: continue
        rc=net.rpc('eth_getTransactionReceipt',[tx],ch)
        rec=h['recipient'].lower()
        for l in rc['logs']:
            if l['topics'] and l['topics'][0]==net.TRANSFER and len(l['topics'])==3 and '0x'+l['topics'][2][-40:]==rec and l['data']!='0x':
                seen.setdefault((rec,ch,l['address'].lower()),0)
                seen[(rec,ch,l['address'].lower())]+=int(l['data'],16)
    rows=[]
    for (rec,ch,tok),raw in seen.items():
        now=int(net.rpc('eth_call',[dict(to=tok,data='0x70a08231'+rec[2:].rjust(64,'0')),'latest'],ch),16)
        dec=int(net.rpc('eth_call',[dict(to=tok,data='0x313ce567'),'latest'],ch),16)
        rows.append(dict(address=rec,chain=ch,token=tok,received=raw/10**dec,now=now/10**dec,read_at=time.strftime('%Y-%m-%d %H:%M',time.gmtime())))
        print(s,rec[:12],ch,tok[:10],'received',round(raw/10**dec,2),'now',round(now/10**dec,2),flush=True)
    out[s]=rows
Path('evidence/recipient_balances.json').write_text(json.dumps(out,indent=1))
print('0x58f2',net.nonce('0x58f298e3bf930886ab7639f4d71f892d5f1f0214',1),net.rpc('eth_getCode',['0x58f298e3bf930886ab7639f4d71f892d5f1f0214','latest'],1)[:10],'calls',net.Stats.calls)
