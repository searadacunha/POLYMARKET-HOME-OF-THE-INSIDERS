"""Does the order id on the origin side equal the one in the Polygon payout's calldata, from chain data alone?"""
import json,sys
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
net.RPC[56]=('https://bsc-mainnet.gateway.tatum.io','https://56.rpc.thirdweb.com')
A='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def b58(s):
    n=0
    for c in s: n=n*58+A.index(c)
    return n.to_bytes((n.bit_length()+7)//8,'big').hex()
s4=json.load(open('evidence/thin_step4.json'))['deposits']
out={}
for name,bsc in (('dep2','0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2'),('dep3','0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1')):
    tail=s4[name]['calldata_tail']; rc=net.rpc('eth_getTransactionReceipt',[bsc],56)
    hits=[int(l['logIndex'],16) for l in rc['logs'] if l['address'].lower()=='0x4cd00e387622c35bddb9b4c962c136462338bc31' and tail in l['data'].lower()]
    out[name]=dict(payout_tail=tail,relay_request_id=s4[name]['relay'][0]['id'],origin_tx=bsc,depository_log_with_same_id=hits)
    print(name,tail[:16],'in BSC depository log',hits)
tail=s4['dep1']['calldata_tail']
t=sol.transaction('3tqC6ccwrcS7a7Lfm4k3tkJZN9iTDsGSzY2gP4FY8T1g21tkLMto7DJnXEGhUpGDmqeaCb16VqJ5GkzKiHypwRyW')
datas=[i.get('data') for i in t['transaction']['message']['instructions'] if i.get('data')]+[i.get('data') for g in (t['meta'].get('innerInstructions') or []) for i in g['instructions'] if i.get('data')]
found=[d for d in datas if tail in b58(d)]
logs=[l for l in (t['meta'].get('logMessages') or []) if 'Program data' in l or 'Memo' in l]
out['dep1']=dict(payout_tail=tail,relay_request_id=s4['dep1']['relay'][0]['id'],origin_sig='3tqC6ccw…',instruction_with_same_id=len(found),program_data_logs=len(logs))
print('dep1',tail[:16],'in Solana instruction data',len(found),'of',len(datas),'logs',len(logs))
Path('evidence/thin_ids.json').write_text(json.dumps(out,indent=1))
