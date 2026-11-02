import json,glob,sys
sys.path.insert(0,'.')
from common import *
INFRA_TRADE={'0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e','0x4d97dcd97ec945f40cf65f87097ace5ea0476045','0xe111180000d2663c0091e4f400237545b87b996b','0xab19716584931d81cd9e7763402673a64baa4876','0x5d0f03cf1243a3e21262d6cf844795afd9fff0ad','0xc5d563a36ae78145c45a50134d48a1215220f80a'}
def dec(h):
    try: d=relay_req(h)
    except Exception as e: return None
    q=(d.get('requests') or [None])[0]
    if not q: return None
    dd=q['data']; m=dd.get('metadata',{})
    ci=m.get('currencyIn',{}); co=m.get('currencyOut',{})
    return dict(user=q.get('user'),recip=q.get('recipient'),inSym=ci.get('currency',{}).get('symbol'),inChain=ci.get('currency',{}).get('chainId'),inAmt=ci.get('amountFormatted'),outSym=co.get('currency',{}).get('symbol'),outChain=co.get('currency',{}).get('chainId'),outAmt=co.get('amountFormatted'),inTx=[(t.get('chainId'),t.get('hash')) for t in dd.get('inTxs',[])],outTx=[(t.get('chainId'),t.get('hash')) for t in dd.get('outTxs',[])],id=q.get('id'))
def show(w, minamt=1):
    r=json.load(open(glob.glob(f'out_{w[:10].lower()}*.json')[0]))
    print('=====',r['wallet'])
    for x in r['flows']:
        if x['cp'] in INFRA_TRADE or x['sym'] not in ('USDC.e','USDC','pUSD') or x['amt']<minamt: continue
        d=dec(x['hash'])
        s=f"   {x['t']} {x['dir']:3s} {x['sym']:6s} {x['amt']:>12,.2f} cp={x['cp'][:12]} tx={x['hash']}"
        if d: s+=f"\n        RELAY user={d['user']} recip={d['recip']} {d['inSym']}@{d['inChain']} {d['inAmt']} -> {d['outSym']}@{d['outChain']} {d['outAmt']} inTx={d['inTx']} outTx={d['outTx']}"
        print(s)
if __name__=='__main__':
    for w in sys.argv[1:]: show(w)
