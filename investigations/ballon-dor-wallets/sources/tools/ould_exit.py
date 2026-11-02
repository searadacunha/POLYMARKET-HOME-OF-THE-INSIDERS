import json,sys
sys.path.insert(0,'tools')
import net
c=json.load(open('cases/ouldlm3alem.json'))
tx=[h['tx'] for h in c['exit_chain'] if h['tx'].startswith('0x909d9602d5ad')][0]
rc=net.rpc('eth_getTransactionReceipt',[tx],137)
print(tx,'from',rc['from'],'to',rc['to'],'logs',len(rc['logs']))
for l in rc['logs']:
    if l['topics'] and l['topics'][0]==net.TRANSFER and len(l['topics'])==3:
        print(int(l['logIndex'],16),net.TOKEN_NAME.get(l['address'].lower(),l['address'][:10]),'0x'+l['topics'][1][-40:],'->','0x'+l['topics'][2][-40:],int(l['data'],16)/1e6 if l['data']!='0x' else None)
    else: print(int(l['logIndex'],16),l['address'][:12],(l['topics'] or ['?'])[0][:12])
print('zero-target relations across cases:')
import glob
for f in glob.glob('cases/*.json'):
    d=json.load(open(f))
    for r in d.get('chain_relations',[]):
        if r['target']=='0x'+'0'*40 or r['source']=='0x'+'0'*40: print(' ',d['slug'],r['id'],r['source'][:10],r['target'][:10],r['amount'],r['tx'][:14])
