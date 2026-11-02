import json,collections,sys
from common2 import es
from lab import label
T='0x3b6dcfde35e53fb7dca8571f23286631b5123c5b'
L=json.load(open('labels_combined.json'))
def nm(ch,a):
    if a==T: return 'TRESORERIE'
    if ch==1 and a in L and L[a]['name']: return L[a]['name']
    return ''
OFFALL={'0xdac17f958d2ee523a2206206994597c13d831ec7','0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0xc2132d05d31c914a87c6611c10748aeb04b58e8f','0xaf88d065e77c8cc2239327c5edb3a432268e5831','0xff970a61a04b1ca14834a43f5de4533ebddb5cc8','0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9'}
res={}
for ch,a in [(1,'0x51481afdb423e115b7225dac293af3a42f6abf17'),(1,'0x4ce150784aa1a05645252c443425f4c219d6c74d'),(1,'0xba8c22847ea773cab402d2c6b3489fb1a9ca9313'),(1,'0xff3cf2291fb1e59499a3444e12fb48c028dc8d0c'),(1,'0xeb1d71ae82a1bb7b38218aea41b3cb5343ed53a4'),(1,'0x47ef369e91cb94eec47f34d7834a8b0d68e8ddb6'),(1,'0xd2f3b47f21997e40058ace206db044584ca77109'),(1,'0x959bd5bf330d64d593fc8bfbaf62fdd8f0710e07'),(1,'0xf4c0cfbcfa183a407e53e21d5e821f194f74fddc'),(1,'0xa86b31489d4c8adcae78ba63c10bffc5ae5f13fc'),(1,'0x7af6c270bdeaf19f618cd32081a3df753d503382'),(137,'0x166716c2838e182d64886135a96f1aabca9a9756'),(137,'0xbde2aaa9e8d0afb90d42679c6e391e5c72be5f39'),(42161,'0x463f5d63e5a5edb8615b0e485a090a18aba08578')]:
    r=es(ch,module='account',action='tokentx',address=a,page=1,offset=1000,sort='desc') or []
    o=collections.Counter(); i=collections.Counter(); no=collections.Counter(); ni=collections.Counter()
    for x in r:
        try: v=int(x['value'])/10**int(x['tokenDecimal'])
        except: continue
        if x["contractAddress"].lower() not in OFFALL: continue
        if x['from'].lower()==a: o[x['to'].lower()]+=v; no[x['to'].lower()]+=1
        else: i[x['from'].lower()]+=v; ni[x['from'].lower()]+=1
    lab1=label(ch,a)
    print(f'## {ch} {a} label={lab1[0]!r} rows={len(r)} | {lab1[2][:90]}')
    print('  OUT', [(k[:10],nm(ch,k) or label(ch,k)[0] if v>1e5 else nm(ch,k),round(v),no[k]) for k,v in o.most_common(4)])
    print('  IN ', [(k[:10],nm(ch,k) or label(ch,k)[0] if v>1e5 else nm(ch,k),round(v),ni[k]) for k,v in i.most_common(4)], 'n_senders',len(i))
    res[a]={'ch':ch,'label':lab1,'out':o.most_common(6),'in':i.most_common(6),'n_in':len(i),'n_out':len(o)}
json.dump(res,open('p4_cp.json','w'))
