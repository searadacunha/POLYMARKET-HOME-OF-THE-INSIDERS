import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
net.RPC[56]=('https://bsc-rpc.publicnode.com','https://bsc-dataseed.bnbchain.org','https://bsc.drpc.org')
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
DEP='0x8e43af995577339436e071990e524ebfe6c09865'; BUSDC='0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d'
out={}
# (a) Payout memos against the Polygon escrow ids in the trace.
trace=json.load(open('evidence/traces/thin.json'))
ids={s['tx']:s['order_id'] for s in trace['trace_stops'] if s.get('order_id')}
print('escrow ids',ids)
PAY={'0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e':'rwiu1FRYMBHqQTiXVdqCssrSs8YQZY2my7fLdNXvrBWDG8V4QckoRoirN3WGeSM6sY3XxC7ERwg486zHmLZEsEd','0x5c4d9506a42a1ecb190233847a7baea1f967766873218d042c714fb00bf31b90':'4HRAyjtxWPQ4Dn4yGAr9Hr5uXp4hMyKmiHUonaLosSPjYpT1z2VAFkeyGLk4Es6urGkauByp6Cbs4RFU4opdhk5o','0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c':'3hB2wsiT2GhpJ9k3wajsJTsxpS28HbSuZySnW61RJy5zeVtHqzSakELK66xzrzWGkZ87xZ6Xr8MKoG9SKfBTrY89','0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989':'2UzjMVyoNhLo2tpSeLqGsqBByBjr8Y74LMmvYyuaNbExtF25TCtU29xCKuk372H9SA2K9VLx12sfoqT1eFSgvGW3'}
out['memos']=[]
for tx,sig in PAY.items():
    t=sol.transaction(sig)
    memos=[i.get('parsed') for i in t['transaction']['message']['instructions'] if i.get('program')=='spl-memo']
    order=ids.get(tx)
    match=any(order and order[2:] in str(m).lower().replace('0x','') for m in memos)
    out['memos'].append(dict(polygon_tx=tx,solana_sig=sig,escrow_order=order,memos=memos,same_id=match))
    print('memo',tx[:12],order,memos,'MATCH' if match else 'no match')
# (b) Balances today.
out['balances']={}
for a in ('CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ','EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B','EMu2EAWjzPB9UyarEiXFg9igRiBxpjDtB4omaPTDMqsd'):
    bal=sol.rpc('getBalance',[a])['value']/1e9
    tok=sol.rpc('getTokenAccountsByOwner',[a,dict(programId='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'),dict(encoding='jsonParsed')])['value']
    toks=[(x['pubkey'],x['account']['data']['parsed']['info']['mint'][:6],x['account']['data']['parsed']['info']['tokenAmount']['uiAmount'],x['account']['data']['parsed']['info'].get('delegate')) for x in tok]
    out['balances'][a]=dict(sol=bal,tokens=toks,read_at=time.time())
    print('bal',a,bal,toks)
# (c) Who funded EMu2 and how busy that address is.
t=sol.transaction('3bn5hJNsXAx8'+'') if False else None
s5=json.load(open('evidence/thin_step5.json'))
row=[r for r in s5['solana']['EMu2EAWjzPB9UyarEiXFg9igRiBxpjDtB4omaPTDMqsd']['rows']]
fund=row[0]; print('fund tx',fund['sig'],fund['moves'])
funder=[m['owner'] for m in fund['moves'] if m['delta']<0][0]
sigs=sol.rpc('getSignaturesForAddress',[funder,dict(limit=1000)])
print('funder',funder,'recent sigs',len(sigs),U(sigs[-1]['blockTime']),U(sigs[0]['blockTime']),'per minute',round(len(sigs)/max((sigs[0]['blockTime']-sigs[-1]['blockTime'])/60,.01),1))
acct=sol.rpc('getAccountInfo',[funder,dict(encoding='base64')])
print('funder account owner',(acct.get('value') or {}).get('owner'),'lamports',(acct.get('value') or {}).get('lamports'))
out['funder']=dict(address=funder,sample=len(sigs),span=[sigs[-1]['blockTime'],sigs[0]['blockTime']],tx=fund['sig'],moves=fund['moves'])
out['deposit_on_relay']=dict(tx=row[1]['sig'],moves=row[1]['moves'],programs=row[1]['programs'])
# (d) Relay's published solver and depository addresses.
ch=net.get('https://api.relay.link/chains')
for c in ch.get('chains',[]):
    if c.get('id') in (792703809,56,137):
        keep={k:c.get(k) for k in ('id','name','solverAddresses','depositAddress','protocol','contracts') if k in c}
        print('relay chain',json.dumps(keep)[:600]); out.setdefault('relay_chains',{})[c['id']]=keep
# (e) Who paid the bridge address on BSC: same address, this token, window before each deposit.
out['bsc_in']={}
def find_block(chain,moment):
    lo,hi=1,int(net.rpc('eth_blockNumber',[],chain),16)
    for _ in range(45):
        if hi-lo<=1: break
        mid=(lo+hi)//2
        if net.block_time(mid,chain)<moment: lo=mid
        else: hi=mid
    return hi
for name,moment in (('dep2',1791899226),('dep3',1791916615)):
    hi=find_block(56,moment+5); lo=find_block(56,moment-3*3600)
    rows=[]
    for s in range(lo,hi+1,2000):
        rows+=net.rpc('eth_getLogs',[dict(address=BUSDC,fromBlock=hex(s),toBlock=hex(min(hi,s+1999)),topics=[net.TRANSFER,None,net.pad(DEP)])],56)
    res=[dict(tx=l['transactionHash'],log=int(l['logIndex'],16),block=int(l['blockNumber'],16),at=net.block_time(int(l['blockNumber'],16),56),src='0x'+l['topics'][1][-40:],raw=str(int(l['data'],16))) for l in rows]
    out['bsc_in'][name]=dict(blocks=[lo,hi],rows=res)
    print('BSC in',name,lo,hi,[(U(r['at']),r['src'],int(r['raw'])/1e18,r['tx']) for r in res])
Path('evidence/thin_step6.json').write_text(json.dumps(out,indent=1))
print('calls',net.Stats.calls)
