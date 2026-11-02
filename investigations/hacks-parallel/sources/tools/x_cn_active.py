import chainlib as c, net, json, es
S={'0xdd3d72c53ff982ff59853da71158bf1538b3ceee':'HW3','0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b':'Dep3f3','0xeba88149813bec1cccccfdb0dacefaaa5de94cb1':'HW4?','0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423':'f2020','0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a':'CN22'}
W={'A_0522':'2026-05-22 06:40:45','C_0625':'2026-06-25 05:51:13','D_1029':'2026-10-29 17:10:23'}
for a,n in S.items():
    for ch in (1,137):
        nonce=int(net.rpc('eth_getTransactionCount',[a,'latest'],chain=ch,cache=False),16)
        row=[n,ch,'nonce',nonce]
        if nonce:
            for w,t in W.items():
                t0=c.ts_of(t); b0,b1=c.block_at(t0-86400,ch),c.block_at(t0+86400,ch)
                tx=es.rows('txlist',a,chain=ch,start=b0,end=b1,offset=1000)
                tk=es.rows('tokentx',a,chain=ch,start=b0,end=b1,offset=1000)
                row.append((w,len(tx),len(tk),sum(1 for r in tx if r['from'].lower()==a),sum(1 for r in tk if r['from'].lower()==a)))
        print(row,flush=True)
