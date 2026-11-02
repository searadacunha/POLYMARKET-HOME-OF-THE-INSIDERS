import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
out=dict(deposits={},solana={})
pay={}
s3=None
# 1. Relay's record of each payout into the bridge address.
tx_full={}
for name,prefix,blocks in (('dep1','0x5e7e110a36af',(95347696,95351496)),('dep2','0xe89360cd25e6',(95459014,95462814)),('dep3','0x3a499027534f',(95470605,95474405))):
    rows=[]
    for s in range(blocks[0],blocks[1]+1,1000):
        rows+=net.rpc('eth_getLogs',[dict(fromBlock=hex(s),toBlock=hex(min(blocks[1],s+999)),topics=[net.TRANSFER,None,net.pad('0x8e43af995577339436e071990e524ebfe6c09865')])],137)
    tx=[l['transactionHash'] for l in rows if l['transactionHash'].startswith(prefix)][0]
    tx_full[name]=tx
    time.sleep(20)
    r=net.get('https://api.relay.link/requests/v2',dict(hash=tx),pause=2)
    txo=net.rpc('eth_getTransactionByHash',[tx],137)
    rec=[]
    for q in r.get('requests',[]):
        d=q.get('data',{});m=d.get('metadata',{})
        rec.append(dict(id=q['id'],status=q['status'],user=q.get('user'),recipient=q.get('recipient'),in_txs=[(t.get('chainId'),t.get('hash')) for t in d.get('inTxs',[])],out_txs=[(t.get('chainId'),t.get('hash')) for t in d.get('outTxs',[])],cin=(m.get('currencyIn') or {}).get('currency',{}).get('symbol'),ain=(m.get('currencyIn') or {}).get('amountFormatted'),cinchain=(m.get('currencyIn') or {}).get('currency',{}).get('chainId'),cout=(m.get('currencyOut') or {}).get('currency',{}).get('symbol'),aout=(m.get('currencyOut') or {}).get('amountFormatted'),sender=m.get('sender')))
    out['deposits'][name]=dict(payout_tx=tx,from_=txo['from'],to=txo['to'],calldata_tail=txo['input'][-64:],relay=rec,raw=r if not rec else None)
    print(name,tx,'solver from',txo['from'],'tail',txo['input'][-64:],json.dumps(rec)[:900],'' if rec else json.dumps(r)[:300])
# 2. Solana side.
SIGS={'CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ':['3hB2wsiT2GhpJ9k3wajsJTsxpS28HbSuZySnW61RJy5zeVtHqzSakELK66xzrzWGkZ87xZ6Xr8MKoG9SKfBTrY89','rwiu1FRYMBHqQTiXVdqCssrSs8YQZY2my7fLdNXvrBWDG8V4QckoRoirN3WGeSM6sY3XxC7ERwg486zHmLZEsEd'],'EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B':['2UzjMVyoNhLo2tpSeLqGsqBByBjr8Y74LMmvYyuaNbExtF25TCtU29xCKuk372H9SA2K9VLx12sfoqT1eFSgvGW3','4HRAyjtxWPQ4Dn4yGAr9Hr5uXp4hMyKmiHUonaLosSPjYpT1z2VAFkeyGLk4Es6urGkauByp6Cbs4RFU4opdhk5o']}
for addr,payouts in SIGS.items():
    sigs,complete=sol.signatures(addr,limit=200,max_pages=2)
    print('SOL',addr,'sigs',len(sigs),'complete',complete,'first',U(sigs[-1]['blockTime']) if sigs else None,'last',U(sigs[0]['blockTime']) if sigs else None)
    rows=[]
    for s in reversed(sigs[-40:] if len(sigs)>40 else sigs):
        tx=sol.transaction(s['signature'])
        mv=sol.token_moves(tx); nat=sol.native_moves(tx)
        prog=sorted({(i.get('program') or i.get('programId','')[:8]) for i in tx['transaction']['message']['instructions']})
        rows.append(dict(sig=s['signature'],at=s['blockTime'],err=s.get('err'),moves=mv,native=nat,programs=prog))
        mine=[m for m in mv if m['owner']==addr]
        print(' ',U(s['blockTime']),s['signature'][:14],'err' if s.get('err') else '', 'mine',[(m['mint'][:6],round(m['delta'],4)) for m in mine],'others',[(str(m['owner'])[:10],m['mint'][:6],round(m['delta'],4)) for m in mv if m['owner']!=addr][:4],'native',[(n['owner'][:10],round(n['delta'],3)) for n in nat][:4],prog[:4])
    out['solana'][addr]=dict(signatures=len(sigs),complete=complete,rows=rows,payouts=payouts)
Path('evidence/thin_step4.json').write_text(json.dumps(out,indent=1))
print('calls',net.Stats.calls)
