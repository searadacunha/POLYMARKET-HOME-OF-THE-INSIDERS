import json,time,httpx,gzip,glob,os
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
cases={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob(I+'cases/*.json')}
def info(base,a):
    try:
        r=http.get(f'{base}/api/v2/addresses/{a}');c=http.get(f'{base}/api/v2/addresses/{a}/counters')
        if r.status_code!=200:return f'HTTP {r.status_code}'
        d=r.json();n=c.json() if c.status_code==200 else {}
        return dict(name=d.get('name'),contract=d.get('is_contract'),verified=d.get('is_verified'),impl=[x.get('name') for x in d.get('implementations') or []],txs=n.get('transactions_count'),native=int(d.get('coin_balance') or 0)/1e18)
    except Exception as e:return 'ERR '+str(e)[:60]
for net,base,a in(('polygon','https://polygon.blockscout.com','0xdc264714f68d84cf29bc605589405e78bdbe7c9f'),('polygon','https://polygon.blockscout.com','0x663dc15d3c1ac63ff12e45ab68fea3f0a883c251'),('polygon','https://polygon.blockscout.com','0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'),('polygon','https://polygon.blockscout.com','0x0ce9bdf38714143043b1d36de9bd90f7335bf06d'),('ethereum','https://eth.blockscout.com','0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165')):
    print(net,a,info(base,a));time.sleep(.5)
# Fallback for Polygon: code and nonce from a public node
for a in('0xdc264714f68d84cf29bc605589405e78bdbe7c9f','0x663dc15d3c1ac63ff12e45ab68fea3f0a883c251','0x0ce9bdf38714143043b1d36de9bd90f7335bf06d'):
    b=http.post('https://polygon-bor-rpc.publicnode.com',json=[dict(jsonrpc='2.0',id=1,method='eth_getCode',params=[a,'latest']),dict(jsonrpc='2.0',id=2,method='eth_getBalance',params=[a,'latest'])]).json()
    code=b[0]['result'];print(a,'code bytes',(len(code)-2)//2,'native POL',int(b[1]['result'],16)/1e18);time.sleep(.3)
out=json.load(open('/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/a12_follow.json'))
print('POL out',json.dumps(out.get('pol_out'))[:500])
tx=[x['tx'] for x in out['pol_out'] if x['pol']>1000][0]
t=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionByHash',params=[tx])).json()['result']
print(tx,'to',t['to'],'value',int(t['value'],16)/1e18,'input',t['input'][:74])
print('\nS_A statuses')
p='/Users/benjamindacunha/Projects/PolySentinel/studies/pipeline_replay_20261101/derived/interim_R3_S_A_20261101.json.gz'
d=json.load(gzip.open(p,'rt'));print(list(d)[:10])
s=json.dumps(d)
for slug,c in sorted(cases.items()):
    a=c['address'].lower();print(' ',slug,'present' if a in s.lower() else 'absent')
print(json.dumps(d,ensure_ascii=False)[:1100])
