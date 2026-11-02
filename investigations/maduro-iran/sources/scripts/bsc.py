import json,urllib.request,time,sys
RPCS=['https://bsc.blockrazor.xyz','https://bsc.blockrazor.xyz','https://bsc-dataseed.bnbchain.org']
def call(m,p):
    err=None
    for i in range(9):
        rpc=('https://bsc.blockrazor.xyz' if m=='eth_getLogs' else ['https://bsc-dataseed.bnbchain.org','https://bsc-dataseed1.defibit.io'][i%2])
        try:
            r=urllib.request.urlopen(urllib.request.Request(rpc,data=json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),headers={'Content-Type':'application/json','User-Agent':'curl/8.4.0'}),timeout=30)
            d=json.loads(r.read())
            if 'error' in d: raise RuntimeError(d['error'])
            return d['result']
        except Exception as e: err=e; time.sleep(1.5)
    raise RuntimeError(err)
def bts(n): return int(call('eth_getBlockByNumber',[hex(n),False])['timestamp'],16)
def find(t):
    hi=int(call('eth_blockNumber',[]),16); lo=hi-40_000_000
    while hi-lo>1:
        mid=(lo+hi)//2
        if bts(mid)<t: lo=mid
        else: hi=mid
    return hi
TOP='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def transfers(a,t,before=3600,after=600,direction='in'):
    b0=find(t-before); b1=find(t+after); logs=[]
    s=b0
    while s<=b1:
        e=min(s+499,b1)
        topics=[TOP,None,'0x000000000000000000000000'+a[2:].lower()] if direction=='in' else [TOP,'0x000000000000000000000000'+a[2:].lower()]
        logs+=call('eth_getLogs',[{'fromBlock':hex(s),'toBlock':hex(e),'topics':topics}]); s=e+1
    return b0,b1,logs
if __name__=='__main__':
    a=sys.argv[1]; t=int(sys.argv[2]); d=sys.argv[3] if len(sys.argv)>3 else 'in'
    b0,b1,logs=transfers(a,t,direction=d)
    print('=====',a,d,'blocks',b0,b1,'n',len(logs))
    for lg in logs:
        v=int(lg['data'],16)/1e18 if lg['data']!='0x' else 0
        print('   blk',int(lg['blockNumber'],16),'token',lg['address'],'from','0x'+lg['topics'][1][26:],'to','0x'+lg['topics'][2][26:],'amt',round(v,4),'tx',lg['transactionHash'])
