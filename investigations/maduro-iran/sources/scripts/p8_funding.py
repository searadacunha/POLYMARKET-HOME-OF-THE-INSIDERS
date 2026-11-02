"""Phase 8 : historique de financement Polygon d'un échantillon de wallets (USDC.e et USDC natif, 1er millier de transferts).
Afflux 'de financement' = afflux USDC dont l'expéditeur n'est pas un contrat de trading Polymarket."""
import json,os,sys
from common2 import es
TRADING={'0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e','0xc5d563a36ae78145c45a50134d48a1215220f80a','0xd91e80cf2e7be2e162c6513ced06f1dd0da35296','0x4d97dcd97ec945f40cf65f87097ace5ea0476045'}
TOK={'0x2791bca1f2de4661ed88a30c99a7a9449aa84174':'USDC.e','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':'USDC'}
wallets=json.load(open(sys.argv[1])); K,N=(int(sys.argv[2]),int(sys.argv[3])) if len(sys.argv)>3 else (0,1)
for i,w in enumerate(wallets):
    if i%N!=K: continue
    fp=f'p8/funding/{w}.json'
    if os.path.exists(fp): continue
    res={'inflows':[],'full':{},'first_any':None}
    for ca,sym in TOK.items():
        try: r=es(137,module='account',action='tokentx',address=w,contractaddress=ca,page=1,offset=1000,sort='asc') or []
        except Exception as e: r=[]; res['err']=str(e)[:100]
        res['full'][sym]=len(r)>=1000
        if r:
            t0=int(r[0]['timeStamp']); res['first_any']=t0 if res['first_any'] is None else min(res['first_any'],t0)
            res['last_seen_'+sym]=int(r[-1]['timeStamp'])
        for x in r:
            if x['to'].lower()==w and x['from'].lower() not in TRADING and int(x['value'])>0:
                res['inflows'].append((int(x['timeStamp']),x['from'].lower(),int(x['value'])/1e6,sym,x['hash']))
    res['inflows'].sort()
    json.dump(res,open(fp,'w'))
print('done',K)
