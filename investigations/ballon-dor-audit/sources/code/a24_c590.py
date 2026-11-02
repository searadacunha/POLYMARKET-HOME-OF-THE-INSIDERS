"""Audit: is 0xc590175e a pooled contract? Same measure as the report's for its hubs, around the POL payment. Public reads only."""
import json,time,httpx
http=httpx.Client(timeout=30,trust_env=False)
U='https://polygon-bor-rpc.publicnode.com'
def rpc(m,p):
    for k in range(4):
        b=http.post(U,json=dict(jsonrpc='2.0',id=1,method=m,params=p)).json()
        if 'result' in b:return b['result']
        time.sleep(1+k)
    raise RuntimeError(str(b)[:200])
A='0xc590175e458b83680867afd273527ff58f74c02b'
pad='0x'+'0'*24+A[2:]
LT='0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4';SYS='0x0000000000000000000000000000000000001010';T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
code=rpc('eth_getCode',[A,'latest']);print('code bytes',(len(code)-2)//2,code[:60])
b0=95710603
for name,addr,top in(('native out',SYS,[LT,None,pad]),('USDC out',['0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0x2791bca1f2de4661ed88a30c99a7a9449aa84174'],[T,pad]),('USDC in',['0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0x2791bca1f2de4661ed88a30c99a7a9449aa84174'],[T,None,pad])):
    logs=[]
    for s in range(b0-4500,b0+4500,3000):
        logs+=rpc('eth_getLogs',[dict(address=addr,fromBlock=hex(s),toBlock=hex(s+2999),topics=top)]);time.sleep(.2)
    idx=3 if name=='native out' else (2 if 'out' in name else 1)
    other={l['topics'][idx] for l in logs}
    print(name,'in 9000 blocks (about 5 h):',len(logs),'distinct counterparties',len(other))
tx=rpc('eth_getTransactionReceipt',['0x4b89cf4f04f9ce694b9dc26bc870fd873a5e00aa71ce1d3e99fd556a75005ac8'])
print('logs in the 59 POL tx',len(tx['logs']),[(l['address'][:10],l['topics'][0][:10]) for l in tx['logs']][:10])
p=[(('0x'+l['topics'][2][-40:])[:10],('0x'+l['topics'][3][-40:])[:10],round(int(l['data'][2:66],16)/1e18,3)) for l in tx['logs'] if l['address'].lower()==SYS]
print('native moves',p)
print('USDC moves',[(l['address'][:8],('0x'+l['topics'][1][-40:])[:10],('0x'+l['topics'][2][-40:])[:10],int(l['data'][:66],16)/1e6) for l in tx['logs'] if l['topics'][0]==T][:8])
