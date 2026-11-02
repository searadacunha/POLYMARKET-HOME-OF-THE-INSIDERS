import json,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net
THIN='0x8d3319c51520518ad01f6744486ceea29f376f5b'; DEP='0x8e43af995577339436e071990e524ebfe6c09865'; OWNER='0x1bf0b469f7f3612657e99bf785e470eee2a76028'
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t))
st=net.get('https://bridge.polymarket.com/status/'+DEP)
print('bridge status',json.dumps(st)[:2500])
print('intermediate is contract?',net.is_contract(DEP),'nonce',net.nonce(DEP),'owner contract?',net.is_contract(OWNER),'owner nonce',net.nonce(OWNER))
rows=[]
for off in range(0,3000,500):
    page=net.get('https://data-api.polymarket.com/activity',dict(user=THIN,limit=500,offset=off,sortBy='TIMESTAMP',sortDirection='ASC'))
    if not isinstance(page,list): print('stop',page); break
    rows+=page
    if len(page)<500: break
print('activity rows',len(rows))
Path('evidence/raw_activity_thin.json').write_text(json.dumps([{k:v for k,v in r.items() if k not in('icon','profileImage','profileImageOptimized','bio')} for r in rows],indent=0))
for r in rows:
    print(U(r['timestamp']),r['type'],r.get('side'),round(r.get('usdcSize') or 0,2),round(r.get('size') or 0,2),r.get('price'),(r.get('title') or '')[:48],r.get('outcome'),r['transactionHash'][:12])
