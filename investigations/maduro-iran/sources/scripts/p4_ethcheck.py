import json,datetime as dt
from deep_evm import pull
FAM={'0x3b6dcfde35e53fb7dca8571f23286631b5123c5b','0x4a9a16755a6bf64291cd2c9eb027b39c129ff58d','0xb7152d5900da932b7fc3cac97aebfc815f88d5ca','0xb93e3d70ac9cacd51764f09ae0d01b905dc291e1','0x26c50e673fca05131c9b9f23d213b977d9a34c77','0x7f227df284f35e5a244603bb1e10814c1766bf63','0xabe7931e45593679a9433add2686706a5134bf2f','0xf4c0cfbcfa183a407e53e21d5e821f194f74fddc','0xba8c22847ea773cab402d2c6b3489fb1a9ca9313','0x0e9e39190df7a2d38872736910cddfa519e419ca','0x974413b8c1d9eeb96758f9d4b5093ea12b3eef54','0x9bdbbd6ff7889e1cb668c21c5da3c8a73a7742ae'}
n=[json.loads(l) for l in open('bfs2/nodes.jsonl')]
T=[x['addr'].lower() for x in n if x['addr'].startswith('0x') and x['kind'] in ('EVM','PM')]
T+=['0x420d62bfb30d22eb6c8449d3b5b09fef1de74b28','0x2c547073a5e46e0a8117117de307a65faa2fac3a' ,'0x2e473c0af74b294031c1ef44b5a3870b47d4d26f']
T=list(dict.fromkeys(T))
hits=[];big=[]
for a in T:
    for act in ('txlist','txlistinternal','tokentx'):
        rows,trunc=pull(1,act,a,maxcalls=3)
        if trunc: big.append((a,act))
        for x in rows:
            if x['from'].lower() in FAM and x['to'].lower()==a and int(x['value'])>0:
                hits.append((dt.datetime.fromtimestamp(int(x['timeStamp']),dt.UTC).strftime('%Y-%m-%d %H:%M:%S'),x['from'].lower(),a,int(x['value'])/10**int(x.get('tokenDecimal') or 18),x.get('tokenSymbol','ETH'),x.get('contractAddress',''),x['hash'],act))
json.dump({'targets':T,'hits':sorted(set(hits)),'big':big},open('p4_ethcheck.json','w'))
print('targets',len(T),'big',big)
for h in sorted(set(hits)): print(h)
