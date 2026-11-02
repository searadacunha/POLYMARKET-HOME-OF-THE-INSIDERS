import chainlib as c, tokens, labels, collections, json
SAFEPATH='0x3cafc13213f9eed5ac1333ae3eb9c7d4e5d34188'
win0=c.ts_of('2026-05-22 08:00:00'); win1=c.ts_of('2026-07-15 00:00:00')
for a,n in (('0x2d507657ca4ebcc8f9a38f6764c07310b66dea54','treasury'),('0x871d7c0f9e19001fc01e04e6cdfa7fa20f929082','871d'),('0xf61e39c7eb1e2ff5af3a24bca88d40fd11594805','f61e')):
    e,cut=c.all_edges(a,137,c.block_at(win0),c.block_at(win1),cap=6000)
    inn=[x for x in e if x['dst']==a and tokens.worth_following(137,x) and win0<=x['ts']<win1]
    ag=collections.defaultdict(lambda:[0,0.0,None])
    for x in inn:
        g=ag[(x['src'],tokens.canonical_symbol(137,x))]; g[0]+=1; g[1]+=c.amount(x); g[2]=g[2] or c.utc(x['ts'])
    m=labels.metadata(list({k[0] for k in ag}),137)
    print(n,'in rows',len(inn),'cut',cut)
    for k,v in sorted(ag.items(),key=lambda kv:-kv[1][1]):
        usd=v[1]*(0.0925 if k[1] in('POL','WPOL') else 1)
        if usd<200000: print('   ',k[0],k[1],v[0],round(v[1],2),v[2],[y['name'] for y in labels.lookup(k[0],137,m)][:2])
