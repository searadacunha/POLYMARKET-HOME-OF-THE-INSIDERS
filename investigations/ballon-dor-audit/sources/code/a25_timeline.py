"""Audit: chronology of the two keys around the 4 October transfer, and of what each did next. Public reads only."""
import json,time,httpx
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
K={'brace227':'0xc852b0938f5ad79b640d105ed11c14499454af26','kraben006':'0x101b5f4dc0886c32e2b75972101aeaf9f338fb65'}
def pages(a,kind,flt=None,maxp=6):
    out=[];params={'filter':flt} if flt else {}
    for _ in range(maxp):
        r=http.get(f'https://eth.blockscout.com/api/v2/addresses/{a}/{kind}',params=params)
        if r.status_code!=200:break
        d=r.json();out+=d.get('items',[])
        if not d.get('next_page_params'):break
        params=dict(d['next_page_params'],**({'filter':flt} if flt else {}));time.sleep(.25)
    return out
for name,a in K.items():
    txs=pages(a,'transactions');ints=pages(a,'internal-transactions','to')
    rows=[(x['timestamp'][:19],'tx',x['from']['hash'][:10],(x.get('to') or {}).get('hash','')[:10],round(int(x['value'])/1e18,6),x.get('method')) for x in txs]
    rows+=[(x['timestamp'][:19],'int',x['from']['hash'][:10],(x.get('to') or {}).get('hash','')[:10],round(int(x['value'])/1e18,6),None) for x in ints if int(x.get('value') or 0)>0]
    rows.sort()
    print('\n',name,a,'rows',len(rows))
    old=[r for r in rows if r[0]<'2026-09-20']
    print(' before 20 Sept: count',len(old),'last',old[-1][0] if old else None)
    for r in rows:
        if '2026-09-20'<=r[0]<='2026-10-10':print('  ',r)
