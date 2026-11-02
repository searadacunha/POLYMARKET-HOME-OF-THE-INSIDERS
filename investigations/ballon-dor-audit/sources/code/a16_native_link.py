"""Audit: the native transfers between the keys of brace227 and kraben006, read from two independent sources. Public reads only."""
import json,time,sys
import httpx
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
K='0x101b5f4dc0886c32e2b75972101aeaf9f338fb65';B='0xc852b0938f5ad79b640d105ed11c14499454af26'
base='https://eth.blockscout.com/api/v2/addresses/'
def paged(addr,kind,flt,maxp=6):
    out,params=[],{'filter':flt}
    for _ in range(maxp):
        r=http.get(f'{base}{addr}/{kind}',params=params)
        if r.status_code!=200:break
        d=r.json();out+=d.get('items',[])
        if not d.get('next_page_params'):break
        params=dict(d['next_page_params'],filter=flt);time.sleep(.3)
    return out
found=[]
for a,b,name in((B,K,'brace227 key -> kraben006 key'),(K,B,'kraben006 key -> brace227 key')):
    for kind,flt in(('transactions','to'),('internal-transactions','to')):
        for x in paged(b,kind,flt):
            if (x.get('from') or {}).get('hash','').lower()==a:
                h=x.get('hash') or x.get('transaction_hash')
                found.append(dict(dir=name,kind=kind,tx=h,value_eth=int(x.get('value') or 0)/1e18,at=x.get('timestamp'),status=x.get('status') or x.get('result'),block=x.get('block') or x.get('block_number')))
    tt=[t for t in paged(b,'token-transfers','to') if (t.get('from') or {}).get('hash','').lower()==a]
    for t in tt:
        found.append(dict(dir=name,kind='token',token=(t.get('token') or {}).get('symbol'),amount=(t.get('total') or {}).get('value'),decimals=(t.get('token') or {}).get('decimals'),tx=t.get('transaction_hash'),at=t.get('timestamp')))
for f in found:print(f)
print('total',len(found))
# second source: the transaction itself from a public node
seen=set()
for f in found:
    if f['tx'] in seen:continue
    seen.add(f['tx'])
    for url in('https://ethereum-rpc.publicnode.com','https://eth.drpc.org'):
        try:
            r=http.post(url,json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionByHash',params=[f['tx']])).json().get('result')
            rc=http.post(url,json=dict(jsonrpc='2.0',id=2,method='eth_getTransactionReceipt',params=[f['tx']])).json().get('result')
            if r:
                print(url.split('/')[2],f['tx'],'from',r['from'],'to',r['to'],'value_eth',int(r['value'],16)/1e18,'block',int(r['blockNumber'],16),'status',rc and rc['status'],'input_len',len(r['input']));break
        except Exception as e:print('ERR',str(e)[:80])
    time.sleep(.3)
print('\n=== activity of each key')
for a,name in((B,'brace227 key'),(K,'kraben006 key')):
    info=http.get(base+a).json();c=http.get(base+a+'/counters').json()
    print(name,a,'txs',c.get('transactions_count'),'transfers',c.get('token_transfers_count'),'eth',int(info.get('coin_balance') or 0)/1e18,'contract',info.get('is_contract'))
    txs=paged(a,'transactions','from',maxp=3)
    print(' first outgoing shown',[(t['timestamp'][:16],(t.get('to') or {}).get('hash','')[:10],round(int(t['value'])/1e18,5)) for t in txs[-6:]])
    ins=paged(a,'transactions','to',maxp=3)
    print(' incoming native',[(t['timestamp'][:16],t['from']['hash'][:10],round(int(t['value'])/1e18,5),t.get('method')) for t in ins if int(t['value'])>0][:12])
