import json,sys,time,urllib.request,urllib.parse
sys.path.insert(0,'tools')
import net
a='0x64cdaa89629fe003eaa31b480d8b63372d109a53'
start,end=26200000,26200300
for name,base,extra in (('blockscout','https://eth.blockscout.com/api',{}),('etherscan','https://api.etherscan.io/v2/api',dict(chainid=1))):
    for off in (1000,10000):
        p=dict(module='account',action='tokentx',address=a,startblock=start,endblock=end,page=1,offset=off,sort='asc',**extra)
        if name=='etherscan': p['apikey']=net._key_from_env()
        t=time.time()
        try:
            body=urllib.request.urlopen(urllib.request.Request(base+'?'+urllib.parse.urlencode(p),headers={'User-Agent':'PolySentinel-ChangeNOW-outflows/0.1 public-read-only'}),timeout=90).read()
            d=json.loads(body); r=d.get('result') or []
            print(name,off,'status',d.get('status'),d.get('message'),'rows',len(r),'bytes',len(body),'s',round(time.time()-t,1), sorted(r[0].keys())[:30] if r and off==1000 else '', r[0]['blockNumber'] if r else '', r[-1]['blockNumber'] if r else '',flush=True)
        except Exception as e:
            print(name,off,'ERR',type(e).__name__,str(e)[:100],round(time.time()-t,1),flush=True)
