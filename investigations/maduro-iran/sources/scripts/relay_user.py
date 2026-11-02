import sys,json
sys.path.insert(0,'.')
from common import *
def relay_by_user(u, maxpages=20):
    out=[]; cont=None
    for i in range(maxpages):
        url=f'https://api.relay.link/requests/v2?user={u}&limit=50'+(f'&continuation={cont}' if cont else '')
        d=http(url,cache=True,min_gap=0.4)
        rq=d.get('requests',[]); out+=rq
        cont=d.get('continuation')
        if not cont or not rq: break
    return out
def summ(q):
    dd=q['data']; m=dd.get('metadata',{}); ci=m.get('currencyIn',{}); co=m.get('currencyOut',{})
    return f"{q.get('createdAt','')[:19]} {q.get('status'):8s} {ci.get('currency',{}).get('symbol')}@{ci.get('currency',{}).get('chainId')} {float(ci.get('amountFormatted') or 0):>12,.2f} -> {co.get('currency',{}).get('symbol')}@{co.get('currency',{}).get('chainId')} recip={q.get('recipient')}"
if __name__=='__main__':
    for u in sys.argv[1:]:
        rq=relay_by_user(u)
        print(f'===== user={u} requests={len(rq)}')
        for q in sorted(rq,key=lambda q:q.get('createdAt','')): print('  ',summ(q))
