"""Exploratory, after the seal of part A. What the eleven named wallets actually held together, from their complete activity."""
import gzip,json,sys,time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,'tools')
import identities as I
ROOT=Path('.')
T_FIN=1792768669;D2=1791917460;T_END=1793044800
U=lambda t:time.strftime('%m-%d %H:%M',time.gmtime(t))
per={};outcomes=defaultdict(dict)
for s,v in I.IDS.items():
    rows=[json.loads(l) for l in gzip.open(f'evidence/activity/{s}.jsonl.gz','rt')]
    book=defaultdict(lambda:dict(buy=0.,buys=0.,sell=0.,sells=0.,redeem=0.,first=None,buy_before_d2=0.,buy_before_article=0.,buy_before_cer=0.))
    for r in rows:
        if r['type'] not in('TRADE','REDEEM','MERGE','SPLIT'):continue
        k=(r.get('title') or '',r.get('outcome') or '')
        b=book[k];size=float(r.get('size') or 0);usd=float(r.get('usdc_size') or 0);t=r['timestamp']
        if r['type']=='TRADE' and r['side']=='BUY':
            b['buy']+=usd;b['buys']+=size;b['first']=min(b['first'] or t,t)
            if t<D2:b['buy_before_d2']+=usd
            if t<T_FIN:b['buy_before_article']+=usd
            if t<T_END:b['buy_before_cer']+=usd
        elif r['type']=='TRADE':b['sell']+=usd;b['sells']+=size
        elif r['type']=='REDEEM':b['redeem']+=usd
    fam={k:b for k,b in book.items() if ("Ballon d'Or" in k[0] or "Ballon d’Or" in k[0]) and "Women" not in k[0]}
    other={k:b for k,b in book.items() if k not in fam}
    per[s]=dict(markets_family=len(fam),buy_family=round(sum(b['buy'] for b in fam.values()),2),buy_other=round(sum(b['buy'] for b in other.values()),2),markets_other=len(other),redeem_family=round(sum(b['redeem'] for b in fam.values()),2))
    for k,b in fam.items():
        if b['buy']>0: outcomes[k][s]=dict(usd=round(b['buy'],2),shares=round(b['buys'],2),first=b['first'],before_d2=round(b['buy_before_d2'],2),before_article=round(b['buy_before_article'],2),before_ceremony=round(b['buy_before_cer'],2),sold=round(b['sell'],2),redeemed=round(b['redeem'],2))
table=[]
for k,v in outcomes.items():
    table.append(dict(title=k[0],outcome=k[1],wallets=len(v),usd=round(sum(x['usd'] for x in v.values()),2),before_d2=round(sum(x['before_d2'] for x in v.values()),2),before_article=round(sum(x['before_article'] for x in v.values()),2),before_ceremony=round(sum(x['before_ceremony'] for x in v.values()),2),redeemed=round(sum(x['redeemed'] for x in v.values()),2),members={s:x for s,x in sorted(v.items(),key=lambda kv:kv[1]['first'])}))
table.sort(key=lambda r:-r['usd'])
Path('collective/exploratoire/combos.json').write_text(json.dumps(dict(per_wallet=per,outcomes=table),ensure_ascii=False,indent=0))
print('wallet | fam markets | buy family | buy other | markets other | redeem fam')
for s,v in per.items(): print(s.ljust(18),v)
print('\noutcomes held by at least 2 named wallets, by dollars')
for r in table:
    if r['wallets']>=2: print(r['wallets'],'$',r['usd'],'avD2',r['before_d2'],'avArt',r['before_article'],'avCer',r['before_ceremony'],'rach',r['redeemed'],'|',r['title'][:62],'|',r['outcome'],'|',[(s,U(x['first'])) for s,x in list(r['members'].items())[:11]])
tot=sum(r['usd'] for r in table);print('total buys family',round(tot,2),'n outcomes',len(table),'single wallet outcomes',sum(1 for r in table if r['wallets']==1))
