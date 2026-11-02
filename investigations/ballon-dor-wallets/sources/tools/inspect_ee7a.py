import json,sys,time,collections
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t)) if t else None
E='0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055'
out={}
USDC={137:[net.TOKENS['USDC.e'],net.TOKENS['USDC']],42161:['0xaf88d065e77c8cc2239327c5edb3a432268e5831']}
def rc_view(tx,ch):
    rc=net.rpc('eth_getTransactionReceipt',[tx],ch); t=net.rpc('eth_getTransactionByHash',[tx],ch)
    L=[]
    for l in rc['logs']:
        if l['topics'] and l['topics'][0]==net.TRANSFER and len(l['topics'])==3 and l['data']!='0x':
            L.append((int(l['logIndex'],16),l['address'][:10],'0x'+l['topics'][1][-40:],'0x'+l['topics'][2][-40:],int(l['data'],16)))
    return dict(tx=tx,chain=ch,block=int(rc['blockNumber'],16),sender=rc['from'],to=rc['to'],selector=t['input'][:10],input_len=len(t['input']),n_logs=len(rc['logs']),transfers=L,sender_nonce=net.nonce(rc['from'],ch))
A=rc_view('0x2c0d0943a7874d99abbc28c4d4930407c8eaad006df45655f6e3ad0c2b808db3',137); B=rc_view('0xc579ce36eea56ec37480b2d3c268f1a137af674c3cdc55c2d33f382a00840a32',42161)
for v in (A,B):
    print('TX',v['chain'],v['tx'][:14],'from',v['sender'],'nonce',v['sender_nonce'],'to',v['to'],'sel',v['selector'],'logs',v['n_logs'])
    for t in v['transfers']: print('   ',t)
out['txs']=[A,B]
# Traffic of this contract, 6 hours each side of each event: a service would show many counterparties.
for name,v in (('wen',A),('ould',B)):
    ch=v['chain']; at=net.block_time(v['block'],ch)
    def bl(m):
        lo,hi=1,int(net.rpc('eth_blockNumber',[],ch),16)
        for _ in range(40):
            if hi-lo<=1: break
            mid=(lo+hi)//2
            if net.block_time(mid,ch)<m: lo=mid
            else: hi=mid
        return hi
    lo,hi=bl(at-6*3600),bl(at+6*3600)
    ins,outs=[],[]
    for s in range(lo,hi+1,9000):
        args=dict(address=USDC[ch],fromBlock=hex(s),toBlock=hex(min(hi,s+8999)))
        outs+=net.rpc('eth_getLogs',[dict(args,topics=[net.TRANSFER,net.pad(E)])],ch)
        ins+=net.rpc('eth_getLogs',[dict(args,topics=[net.TRANSFER,None,net.pad(E)])],ch)
    print(name,'chain',ch,'blocks',hi-lo,'12h window: outflows',len(outs),'inflows',len(ins),'distinct receivers',len({l['topics'][2] for l in outs}),'distinct payers',len({l['topics'][1] for l in ins}))
    print('   outs',[(U(net.block_time(int(l['blockNumber'],16),ch)),'0x'+l['topics'][2][-40:],int(l['data'],16)/1e6) for l in outs][:10])
    print('   ins',[(U(net.block_time(int(l['blockNumber'],16),ch)),'0x'+l['topics'][1][-40:],int(l['data'],16)/1e6) for l in ins][:10])
    out[name]=dict(chain=ch,blocks=[lo,hi],outflows=len(outs),inflows=len(ins),receivers=sorted({l['topics'][2] for l in outs}),payers=sorted({l['topics'][1] for l in ins}))
print('impl code bytes',(len(net.rpc('eth_getCode',['0xd206ac7fef53d83ed4563e770b28dba90d0d9ec8','latest'],137))-2)//2)
# Gxjc: what came out right after the two named deposits.
G='GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
MINT={'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v':'USDC','Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB':'USDT'}
out['gxjc']={}
targets={'cookedrice':'5jAnEGy7ZFNQCkWBWNXSVwU8K6FqvBLCtPyAA2Ls9NoTa85uj7WLAVdUQPrmkdbHD9mF4i1nfCcbLmd53WhrtVkJ','vidente':'2UCgkFYwUKGceXb1VXABUFTUZiNrwUgUh6vDPDr9ae2MN9SEFB8GqLikvoHueeuavaoQ3AQspG72L8fiwd78LQRq'}
page=[];before=None;left=dict(targets)
for i in range(22):
    p=sol.rpc('getSignaturesForAddress',[G,dict(limit=1000,**({'before':before} if before else {}))])
    page+=p; before=p[-1]['signature']
    idx={s['signature']:k for k,s in enumerate(page)}
    if all(v in idx for v in targets.values()): break
print('paged',i+1,'sigs',len(page),'oldest',U(page[-1]['blockTime']))
idx={s['signature']:k for k,s in enumerate(page)}
for name,sig in targets.items():
    k=idx.get(sig)
    if k is None:
        print(name,'not reached'); out['gxjc'][name]=dict(found=False); continue
    t0=page[k]['blockTime']
    nearby=[page[j] for j in range(max(0,k-14),k+1)]
    rows=[]
    for s in reversed(nearby):
        t=sol.transaction(s['signature'])
        mv=sol.token_moves(t)
        me=[(MINT.get(m['mint'],m['mint'][:5]),round(m['delta'],2)) for m in mv if m['owner']==G]
        ot=[(str(m['owner']),MINT.get(m['mint'],m['mint'][:5]),round(m['delta'],2)) for m in mv if m['owner']!=G]
        prog=sorted({(i.get('program') or i.get('programId','')[:8]) for i in t['transaction']['message']['instructions']})
        memo=[i.get('parsed') for i in t['transaction']['message']['instructions'] if i.get('program')=='spl-memo']
        rows.append(dict(sig=s['signature'],at=s['blockTime'],me=me,others=ot,programs=prog,memo=memo))
        print(name,U(s['blockTime']),s['signature'][:10],'me',me,'others',ot[:3],prog[:5],memo)
    out['gxjc'][name]=dict(found=True,rows=rows)
Path('evidence/hub_ee7a_gxjc.json').write_text(json.dumps(out,indent=1)); print('calls',net.Stats.calls)
