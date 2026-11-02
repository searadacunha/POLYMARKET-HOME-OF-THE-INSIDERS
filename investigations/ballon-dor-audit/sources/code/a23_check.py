import json,time,httpx
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/';I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
hits=json.load(open(OUT+'a22_polygon_native.json'))
print('across',[h for h in hits if h['src_case']!=h['dst_case']])
from collections import Counter
print('within',Counter((h['src'][:10],h['dst'][:10],h['src_case']) for h in hits if h['src_case']==h['dst_case']).most_common(8))
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
for a in('0xc590175e458b83680867afd273527ff58f74c02b','0x408ce42ac7538e5a6f53324585075470d1b3c5b3'):
    print(a[:10],[(r['case'],r['category'],(r['source'] or '')[:10],(r['target'] or '')[:10],r['token'],r['amount'],r['utc'],r['basis'][:110]) for r in rel if a in((r['source'] or '').lower(),(r['target'] or '').lower())][:5])
across=[h for h in hits if h['src_case']!=h['dst_case']]
for h in across:
    t=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionByHash',params=[h['tx']])).json()['result']
    print(h['tx'],'tx from',t['from'],'to',t['to'],'value',int(t['value'],16)/1e18,'input',t['input'][:12],'block',h['block'])
def nonce(a,url):
    return int(http.post(url,json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionCount',params=[a,'latest'])).json()['result'],16)
for a in('0xc590175e458b83680867afd273527ff58f74c02b','0x408ce42ac7538e5a6f53324585075470d1b3c5b3'):
    print(a[:10],'polygon nonce',nonce(a,'https://polygon-bor-rpc.publicnode.com'),'ethereum nonce',nonce(a,'https://ethereum-rpc.publicnode.com'))
print()
for a in('0xc066ac5d385419b1a8c43a0e146fa439837a8b8c','0xe3478b0bb1a5084567c319096437924948be1964','0x84435610b13ff72df2359cedb302286cdf8bf1e3','0xf70da97812cb96acdf810712aa562db8dfa3dbef'):
    d=http.get('https://eth.blockscout.com/api/v2/addresses/'+a).json();c=http.get('https://eth.blockscout.com/api/v2/addresses/'+a+'/counters').json()
    print(a[:10],'name',d.get('name'),'contract',d.get('is_contract'),'txs',c.get('transactions_count'),'transfers',c.get('token_transfers_count'),'nonce',nonce(a,'https://ethereum-rpc.publicnode.com'))
    time.sleep(.3)
e=json.load(open(OUT+'a17_keys.json'))
print('errors',e['errors'][:30]);print('capped',sorted(set(x[0] for x in e['capped'])))
for o in('0xe3478b0bb1a5084567c319096437924948be1964','0xc066ac5d385419b1a8c43a0e146fa439837a8b8c'):
    print('\n',o[:10])
    for x in e['edges']:
        if x['other']==o:print('  ',x['at'][:19],x['cases'],x['a'][:10],x['kind'][:5],x['flt'],x['token'] or 'native',x['value']/10**int(x['dec'] or 18),x['tx'][:14])
