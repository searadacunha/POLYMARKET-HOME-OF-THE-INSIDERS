import json,sys,time
sys.path.insert(0,'tools')
import net
tx='0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c'
for url in ('https://api.relay.link/requests/v3',):
    for q in (dict(hash=tx),dict(txHash=tx),dict(user='0x8d3319c51520518ad01f6744486ceea29f376f5b')):
        try:
            r=net.get(url,q,pause=2,retries=1); print(url,q,json.dumps(r)[:1200])
        except Exception as e: print(url,q,'ERR',e)
