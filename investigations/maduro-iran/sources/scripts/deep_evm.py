import sys,json,os,datetime as dt; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common2 import es
def pull(chain, action, a, maxcalls=400):
    out=[]; start=0; calls=0
    while calls<maxcalls:
        r=es(chain,module='account',action=action,address=a,startblock=start,endblock=99999999,sort='asc',page=1,offset=1000); calls+=1
        if not r: break
        if len(r)<1000: out+=r; break
        last=int(r[-1]['blockNumber'])
        if last==start: out+=r; start=last+1; continue
        out+=[x for x in r if int(x['blockNumber'])<last]; start=last
    return out, calls>=maxcalls
if __name__=='__main__':
    a=sys.argv[1].lower(); chains=[int(c) for c in sys.argv[2].split(',')]
    for ch in chains:
        for act in ('tokentx','txlist','txlistinternal'):
            rows,trunc=pull(ch,act,a)
            fn=f'deep_{a[:10]}_{ch}_{act}.json'; json.dump(rows,open(fn,'w'))
            print(ch,act,len(rows),'truncated' if trunc else '',flush=True)
