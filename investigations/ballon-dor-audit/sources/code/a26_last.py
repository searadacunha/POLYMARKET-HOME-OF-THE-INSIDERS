import json,time,httpx
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
http=httpx.Client(timeout=30,trust_env=False)
n=json.load(open(OUT+'a7_native.json'))
from collections import defaultdict
pay=defaultdict(set);fund=defaultdict(set)
for a,r in n['solana'].items():
    for p in r['fee_payers']:pay[p].update(r['cases'])
    for x in r['native_in']:
        for f in x['from']:fund[f].update(r['cases'])
print('fee payers in 2+',{k:sorted(v) for k,v in pay.items() if len(v)>1})
print('native funders in 2+',{k:sorted(v) for k,v in fund.items() if len(v)>1})
for a in('CBXuKTC3JAHjCvUeCXF2mXJazBqATDExQRxZi1iqQcDa',):
    for k in range(5):
        r=http.post('https://api.mainnet-beta.solana.com',json=dict(jsonrpc='2.0',id=1,method='getSignaturesForAddress',params=[a,dict(limit=1000)]))
        if r.status_code==200 and r.json().get('result'):
            s=r.json()['result'];print(a[:10],len(s),'signatures over',round((s[0]['blockTime']-s[-1]['blockTime'])/3600,2),'hours');break
        time.sleep(3)
e=json.load(open('/Users/benjamindacunha/Projects/PolySentinel-investigation/collective/derived/B_E6.json'))
pw=e['per_wallet'];g=e['groups']
for name in('cookedrice',):
    a=[w for w in g['named'] if w.lower()==__import__('json').load(open('/Users/benjamindacunha/Projects/PolySentinel-investigation/cases/cookedrice.json'))['address']][0]
    gap=pw[a]['gap_s']
    rows=[(k,w) for k in('non_surlignes','meme_token','token_oppose') for w in g[k]]
    all_=[pw[w] for k,w in rows if pw.get(w,{}).get('gap_s') is not None]
    comp=[x for x in all_ if x.get('complete')]
    print(name,'gap',gap,'all',sum(x['gap_s']<=gap for x in all_),'of',len(all_),'complete',sum(x['gap_s']<=gap for x in comp),'of',len(comp))
