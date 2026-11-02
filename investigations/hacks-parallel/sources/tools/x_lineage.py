import chainlib as c, net, labels, es, json, pm, glob, re, os
from pathlib import Path
pm.self_check()
T=['0xff4c483c4c7f72f78077527521fce4b2595e454f','0xc0126535cbc6f70fc71d41bbc266d76321159efe','0x8669debfa2b60f73300a95140b02408263cece01']
first=es.rows('txlist',T[1],chain=137,offset=1)[0]; root=first['from'].lower(); T.append(root)
print('root funder',root,c.utc(first['timeStamp']),int(first['value'])/1e18,first['hash'])
d='0xd152f549545093347a162dce210e7293f1452150'
print('d152',labels.metadata([d],137),net.rpc('eth_getCode',[d,'latest'],chain=137)[:8],int(net.rpc('eth_getTransactionCount',[d,'latest'],chain=137),16))
m=labels.metadata(T,137)
for a in T:
    acc=pm.accounts(a)
    print(a,'nonce',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=137),16),'eth',int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=1),16),[y['name'] for y in labels.lookup(a,137,m)][:3],'PM:',[(k,w,(f or {}).get('type'),c.utc(f['timestamp']) if f else None) for k,w,f in acc])
# hits in other investigations, any file type under 20 MB
roots=[Path.home()/'Projects'/p for p in ('PolySentinel-investigation','PolySentinel-flow-trace','PolySentinel-ChangeNOW-proof','PolySentinel-ballon-dor-2026','PolySentinel-audit-20261102','PolySentinel-ChangeNOW-outflows')]+[Path.home()/'Documents/Crypto/cn_pm_sakana']
need=T+['0x8f98075db5d6c620e8d420a8c516e2f2059d9b91','0x91430cad2d3975766499717fa0d66a78d814e5c5','0xe65b1c586757c5510b60f998eebb14c1ef71e1ed','0x3f99139f1c5854bb628c2e576aaf638e99dffc18','0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423','0x6976d8025229db5f54bc899dd3dbc9285423896b','0x89c5151236de544d077fc69813a4db89224ee8a1','0x1e52af24eb770a44c65b906db244ba3de3451dc5','0x71d4249079684479f2651745fa2fcd79c9b45f53','0x3dce0a29139a851da1dfca56af8e8a6440b4d952']
hits={a:[] for a in need}
n=0
for r in roots:
    for p in r.rglob('*'):
        if p.is_file() and p.suffix in ('.csv','.json','.md','.jsonl','.txt','.log') and p.stat().st_size<20_000_000 and 'http_cache' not in str(p) and '.venv' not in str(p):
            n+=1
            try: t=p.read_text(errors='ignore').lower()
            except OSError: continue
            for a in need:
                if a in t: hits[a].append(str(p.relative_to(Path.home())))
print('files scanned',n)
for a,v in hits.items(): print(a,len(v),v[:4])
json.dump(hits,open('../state/runs/lineage_hits.json','w'),indent=1)
