import sys, json, datetime as dt
from collections import defaultdict
sys.path.insert(0,'.')
from common import *
def T(t): return dt.datetime.fromtimestamp(int(t), dt.UTC).strftime('%Y-%m-%d %H:%M')
def hop(chain, a, t0=None, t1=None, minusd=5, show=40):
    a=a.lower()
    tt=es_all(chain,'tokentx',a)
    tx=es_all(chain,'txlist',a)
    itx=es_all(chain,'txlistinternal',a)
    code=es(chain,module='proxy',action='eth_getCode',address=a,tag='latest')
    code=code.get('result') if isinstance(code,dict) else code
    print(f'### chain={chain} {a} code={"CONTRACT/7702" if code and code!="0x" else "EOA"}({len(code or "")}) tokentx={len(tt)} txlist={len(tx)} internal={len(itx)}')
    if tx: print('   first tx', T(tx[0]['timeStamp']), 'last tx', T(tx[-1]['timeStamp']), ' nonce-ish out=', sum(1 for x in tx if x['from'].lower()==a))
    rows=[]
    OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7','0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0xc2132d05d31c914a87c6611c10748aeb04b58e8f','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb','0x833589fcd6edb6e08f4c7c32d4f71b54bda02913','0xfde4c96c8593536e31f229ea8f37b2ada2699bb2','0xaf88d065e77c8cc2239327c5edb3a432268e5831','0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9','0x6b175474e89094c44da98b954eedeac495271d0f','0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'}
    for x in tt:
        if x['contractAddress'].lower() not in OFF: continue
        amt=int(x['value'])/10**int(x['tokenDecimal'] or 0)
        rows.append((int(x['timeStamp']),'IN' if x['to'].lower()==a else 'OUT',x['tokenSymbol'],amt,(x['from'] if x['to'].lower()==a else x['to']).lower(),x['hash']))
    for x in tx+itx:
        v=int(x['value'])/1e18
        if v>0: rows.append((int(x['timeStamp']),'IN' if x['to'].lower()==a else 'OUT','NATIVE',v,(x['from'] if x['to'].lower()==a else x['to']).lower(),x['hash']))
    rows.sort()
    if t0: rows=[r for r in rows if r[0]>=t0]
    if t1: rows=[r for r in rows if r[0]<=t1]
    stable={'USDC','USDC.e','USDT','USDT0','pUSD','DAI','USDe','USDC.E'}
    n=0
    for r in rows:
        usd=r[3] if r[2] in stable else None
        if r[2] in stable and r[3]<minusd: continue
        if r[2] not in stable and r[2]!='NATIVE': 
            if r[3]==0: continue
        print(f'   {T(r[0])} {r[1]:3s} {r[2]:7s} {r[3]:>14,.4f} {r[4]} {r[5]}')
        n+=1
        if n>=show: print('   ... truncated'); break
    return rows
if __name__=='__main__':
    chain=int(sys.argv[1]); a=sys.argv[2]
    t0=int(sys.argv[3]) if len(sys.argv)>3 else None; t1=int(sys.argv[4]) if len(sys.argv)>4 else None
    hop(chain,a,t0,t1)
