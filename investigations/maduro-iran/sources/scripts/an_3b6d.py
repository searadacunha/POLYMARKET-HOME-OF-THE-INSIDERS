import json,datetime as dt,statistics as st
from collections import Counter,defaultdict
A='0x3b6dcfde35e53fb7dca8571f23286631b5123c5b'
STAB={1:{'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'USDC','0xdac17f958d2ee523a2206206994597c13d831ec7':'USDT'},
      137:{'0x2791bca1f2de4661ed88a30c99a7a9449aa84174':'USDC.e','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359':'USDC','0xc2132d05d31c914a87c6611c10748aeb04b58e8f':'USDT0'},
      42161:{'0xaf88d065e77c8cc2239327c5edb3a432268e5831':'USDC','0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9':'USDT0','0xff970a61a04b1ca14834a43f5de4533ebddb5cc8':'USDC.e'}}
T=lambda t: dt.datetime.fromtimestamp(int(t),dt.UTC).strftime('%Y-%m-%d %H:%M')
R={}
for ch in (1,137,42161):
    tt=json.load(open(f'deep_{A[:10]}_{ch}_tokentx.json')); tx=json.load(open(f'deep_{A[:10]}_{ch}_txlist.json'))
    st_=[x for x in tt if x['contractAddress'].lower() in STAB[ch]]
    other=Counter(x['tokenSymbol'] for x in tt if x['contractAddress'].lower() not in STAB[ch])
    ins=[x for x in st_ if x['to'].lower()==A]; outs=[x for x in st_ if x['from'].lower()==A]
    si=defaultdict(float); ni=Counter(); so=defaultdict(float); no=Counter()
    for x in ins: v=int(x['value'])/1e6; si[x['from'].lower()]+=v; ni[x['from'].lower()]+=1
    for x in outs: v=int(x['value'])/1e6; so[x['to'].lower()]+=v; no[x['to'].lower()]+=1
    amts=[int(x['value'])/1e6 for x in outs]
    hours=Counter(int(dt.datetime.fromtimestamp(int(x['timeStamp']),dt.UTC).hour) for x in outs)
    months=Counter(T(x['timeStamp'])[:7] for x in outs)
    print(f'===== chain {ch}: txlist {len(tx)} first {T(tx[0]["timeStamp"]) if tx else None} last {T(tx[-1]["timeStamp"]) if tx else None} sent_by_self {sum(1 for x in tx if x["from"].lower()==A)}')
    print(f'  stable IN n={len(ins)} ${sum(si.values()):,.0f} from {len(si)} senders | OUT n={len(outs)} ${sum(so.values()):,.0f} to {len(so)} recipients | other tokens top {other.most_common(4)}')
    if amts: print(f'  out size median {st.median(amts):,.2f} mean {st.mean(amts):,.2f} p90 {sorted(amts)[int(.9*len(amts))]:,.2f} max {max(amts):,.0f}; top5 recipients share {sum(sorted(so.values())[-5:])/max(1,sum(so.values())):.3f}')
    print('  top senders:',[(k,round(v),ni[k]) for k,v in sorted(si.items(),key=lambda z:-z[1])[:8]])
    print('  top recipients:',[(k,round(v),no[k]) for k,v in sorted(so.items(),key=lambda z:-z[1])[:8]])
    print('  out by UTC hour:',[hours.get(h,0) for h in range(24)])
    print('  out by month:',sorted(months.items())[:14])
    R[ch]=dict(si=si,ni=ni,so=so,no=no)
json.dump({str(k):{kk:(dict(vv) if isinstance(vv,(dict,Counter)) else vv) for kk,vv in v.items()} for k,v in R.items()},open('an_3b6d.json','w'))
