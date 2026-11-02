"""Audit: native POL between the dossiers' addresses, from Polygon's LogTransfer events, the check the report could not make through ERC-20 logs. Same window as its scan. Public reads only."""
import glob,json,os,sys,time
sys.path.insert(0,'/Users/benjamindacunha/Projects/PolySentinel-harness')
os.environ['SIGNAL_ENGINE_STATE']='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/es'
from signal_engine.fund_flow.client import Client
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/';OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
nodes=json.load(open(I+'graphs/links_classified.json'))['nodes'];hubs={n['address'].lower() for n in nodes}
own={}
for s,c in cases.items():
    own[c['address'].lower()]=s
    for o in c['wallet'].get('owners') or []:own[o.lower()]=s
    for x in c.get('recipients',[]):
        if str(x['address']).startswith('0x'):own.setdefault(x['address'].lower(),s)
    for h in c.get('funding_chain',[]):
        if h and h.get('immediate_source') and (h.get('kind') or {}).get('kind')!='CONTRACT':own.setdefault(h['immediate_source'].lower(),s)
for r in (json.loads(l) for l in open(I+'graphs/relations.jsonl')):
    for side in('source','target'):
        a=(r[side] or '').lower()
        if a.startswith('0x') and not r.get(side+'_label') and a not in hubs:own.setdefault(a,r['case'])
print('addresses',len(own),flush=True)
LT='0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4';SYS='0x0000000000000000000000000000000000001010'
P=['0x'+'0'*24+a[2:] for a in own]
c=Client(rpc_limit=400,http_limit=0,pause_s=.2,ledger=OUT+'rpc_requests.jsonl')
lo,hi=94392840,c.head(137);hits=[];errors=0;n=0
for s in range(lo,hi+1,9000):
    try:
        logs=c.rpc('eth_getLogs',[dict(address=SYS,fromBlock=hex(s),toBlock=hex(min(hi,s+8999)),topics=[LT,None,P,P])],137);n+=1
    except Exception as e:
        errors+=1;print('ERR',s,str(e)[:90],flush=True);continue
    for l in logs:
        a,b='0x'+l['topics'][2][-40:],'0x'+l['topics'][3][-40:]
        hits.append(dict(tx=l['transactionHash'],block=int(l['blockNumber'],16),src=a,src_case=own[a],dst=b,dst_case=own[b],pol=int(l['data'][2:66],16)/1e18))
print('chunks',n,'errors',errors,'hits',len(hits),'across dossiers',[h for h in hits if h['src_case']!=h['dst_case']],flush=True)
print('within dossier (positive control)',len([h for h in hits if h['src_case']==h['dst_case']]),[ (h['src_case'],round(h['pol'],3)) for h in hits if h['src_case']==h['dst_case']][:6])
json.dump(hits,open(OUT+'a22_polygon_native.json','w'),indent=0)
rc=c.receipt('0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3',137)
T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
print('swap of 839,000 POL:',[(l['address'][:10],'0x'+l['topics'][1][-40:][:10],'0x'+l['topics'][2][-40:][:10],int(l['data'][:66],16)) for l in rc['logs'] if l['topics'] and l['topics'][0]==T][-8:])
