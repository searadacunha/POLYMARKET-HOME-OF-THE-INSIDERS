import json,sys,datetime as D
from pathlib import Path
sys.path.insert(0,'tools')
import es,net
hubs='0x64cdaa89629fe003eaa31b480d8b63372d109a53 0xd91efec7e42f80156d1d9f660a69847188950747 0x58edf78281334335effa23101bbe3371b6a36a51 0x83c41363cbee0081dab75cb841fa24f3db46627e 0x300773969b499b9768267e0c5a049f7751de79e7 0x45300136662dd4e58fc0df61e6290dffd992b785 0x41e457717052a9f80fb2a5a06caccda18469fb17 0x2458b3ad07e88b78d0204525d9cbf445c22843e7 0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423'.split()
f=lambda t: D.datetime.fromtimestamp(int(t),D.UTC).strftime('%Y-%m-%d %H:%M')
for h in hubs:
    d=net.get('https://metadata.services.blockscout.com/api/v1/metadata',dict(addresses=h,chainId=1),pause=.4)
    tags=[t['name'] for v in d.get('addresses',{}).values() for t in v.get('tags',[])]
    chain=137 if h.startswith('0xf2020') else 1
    a=es.rows('txlist',h,chain,sort='asc',offset=5); b=es.rows('tokentx',h,chain,sort='asc',offset=5)
    code=net.rpc('eth_getCode',[h,'latest'],chain=chain)
    print(h,'tags',tags,'code',len(code)//2-1, code[:10] if len(code)>2 else '', 'first_tx',f(a[0]['timeStamp']) if a else None,a[0]['from'][:12] if a else '', 'first_tok',f(b[0]['timeStamp']) if b else None,b[0]['from'][:12] if b else '',b[0].get('tokenSymbol') if b else '',flush=True)
