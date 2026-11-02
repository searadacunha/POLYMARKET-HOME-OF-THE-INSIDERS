import sys,json,os,time; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common2 import es
TOP='0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6'
EX='0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e'
def blk(t,c): return int(es(137,module='block',action='getblocknobytime',timestamp=t,closest=c))
def scan(name, t0, t1, toks, step=12):
    b0,b1=blk(t0,'after'),blk(t1,'before')
    ck=f'fills_{name}.jsonl'; done=set()
    if os.path.exists(ck):
        for l in open(ck):
            x=json.loads(l)
            if x.get('_range'): done.add(tuple(x['_range']))
    f=open(ck,'a'); tokset={int(v):k for k,v in toks.items()}
    x=b0; total=0
    while x<=b1:
        y=min(x+step-1,b1)
        if (x,y) in done: x=y+1; continue
        rows=[]; ok=True
        for p in range(1,11):
            r=es(137,module='logs',action='getLogs',address=EX,topic0=TOP,fromBlock=x,toBlock=y,page=p,offset=1000)
            rows+=r
            if len(r)<1000: break
            if p==10: ok=False
        if not ok:
            step=max(1,step//2); continue
        total+=len(rows)
        for lg in rows:
            d=lg['data'][2:]; w=[int(d[i:i+64],16) for i in range(0,len(d),64)]
            if w[0] in tokset or w[1] in tokset:
                f.write(json.dumps(dict(block=int(lg['blockNumber'],16),ts=int(lg['timeStamp'],16),tx=lg['transactionHash'],li=int(lg['logIndex'],16),
                    maker='0x'+lg['topics'][2][26:],taker='0x'+lg['topics'][3][26:],mAsset=tokset.get(w[0],'USDC' if w[0]==0 else str(w[0])),
                    tAsset=tokset.get(w[1],'USDC' if w[1]==0 else str(w[1])),mAmt=w[2]/1e6,tAmt=w[3]/1e6,fee=w[4]/1e6))+'\n')
        f.write(json.dumps({'_range':[x,y],'n':len(rows)})+'\n'); f.flush()
        x=y+1
    print(name,'blocks',b0,b1,'logs scanned (this run)',total)
    return b0,b1
if __name__=='__main__':
    mk=json.load(open('markets.json'))
    which=sys.argv[1]
    if len(sys.argv)>4:
        title={'M':'Maduro out by January 31, 2026?','I':'US strikes Iran by February 28, 2026?'}[sys.argv[4]]
        scan(which,int(sys.argv[2]),int(sys.argv[3]),mk[title]['tokens']); sys.exit()
    if which=='maduro': scan('maduro',1767416400,1767420720,mk['Maduro out by January 31, 2026?']['tokens'])
    if which=='iran': scan('iran',1772256480,1772259180,mk['US strikes Iran by February 28, 2026?']['tokens'])
