"""Second look at payout candidates of at least 5 000 $ for the deposits on the ChangeNOW-tagged wallets: is the recipient new, where does the money go next, does it touch the stolen trail?"""
import json,sys,collections
sys.path.insert(0,'.')
import chainlib as c, net, labels, tokens, cn_novelty as nv
cands=json.load(open('../state/runs/match_cands.json'))
trail=set(json.load(open('../state/runs/may_polygon_full.json'))['nodes'])
rows=[]
for x in cands:
    if x['r']['usd']<5000: continue
    e=x['r']['e']; a=e['dst']; ch=x['r']['chain']
    st=nv.status(a,ch,e['ts'])
    b0,b1=c.block_at(e['ts'],ch),c.block_at(e['ts']+14*86400,ch)
    ed,cut=c.all_edges(a,ch,b0,b1,cap=500)
    out=[y for y in ed if y['src']==a and tokens.worth_following(ch,y)]
    ag=collections.defaultdict(float)
    for y in out: ag[(y['dst'],tokens.canonical_symbol(ch,y))]+=c.amount(y)
    top=sorted(ag.items(),key=lambda kv:-kv[1])[:3]
    m=labels.metadata([k[0] for k,_ in top],ch) if top else {}
    r=dict(deposit_tx=x['d']['tx'],deposit_usd=round(x['d']['usd'],2),hub=x['d']['hub'],payout_tx=e['tx'],payout_block=e['block'],payout_utc=c.utc(e['ts']),source=x['r']['source'],chain=ch,recipient=a,asset=tokens.canonical_symbol(ch,e),amount=c.amount(e),usd=round(x['r']['usd'],2),delay_h=round((e['ts']-x['d']['ts'])/3600,2),implied_fee=round(1-x['r']['usd']/x['d']['usd'],4),status=st,in_stolen_trail=a in trail,next_hops=[(k[0],k[1],round(v,2),[z['name'] for z in labels.lookup(k[0],ch,m)][:2]) for k,v in top],out_rows=len(out),cut=cut)
    rows.append(r)
    print(r['deposit_usd'],r['hub'],r['source'],a,r['usd'],r['delay_h'],st,r['in_stolen_trail'],[(n[0][:10],n[1],n[2],n[3][:1]) for n in r['next_hops']][:2],flush=True)
json.dump(rows,open('../state/runs/big_cands.json','w'),indent=1)
