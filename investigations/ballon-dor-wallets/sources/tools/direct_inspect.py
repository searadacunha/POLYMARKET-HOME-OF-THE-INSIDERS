import json,sys,time
sys.path.insert(0,'tools')
import net
U=lambda t:time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(t))
d=json.load(open('graphs/direct_transfers.json'))
for h in d['hits']:
    print(h['chain'],h['kind'],h['source_case'],'->',h['target_case'],h.get('raw'),U(h['at']),h['tx'][:16])
h=[x for x in d['hits'] if x['kind']=='position'][0]
rc=net.rpc('eth_getTransactionReceipt',[h['tx']],137); tx=net.rpc('eth_getTransactionByHash',[h['tx']],137)
print('from',rc['from'],'to',rc['to'],'logs',len(rc['logs']),'sel',tx['input'][:10])
for l in rc['logs']:
    print(int(l['logIndex'],16),l['address'][:12],l['topics'][0][:12],[t[-40:][:12] for t in l['topics'][1:]],len(l['data']))
