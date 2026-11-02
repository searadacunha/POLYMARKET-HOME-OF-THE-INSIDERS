"""Per-case results of the statistical controls, offline, from frozen inputs and sealed outputs. Exploratory: written after results were read. No network."""
import gzip,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,'tools');sys.path.insert(0,'collective/code')
import identities as I, rows as R, signals as K
J=lambda p:json.loads(Path(p).read_text())
ADDR={k:v['address'] for k,v in I.IDS.items()}; SLUG={v:k for k,v in ADDR.items()}
fam=[r for r in R.family() if r[0]=='M']
buys=[r for r in fam if r[4]=='BUY']
cat=R.catalog()
SAME,OPP=J('collective/data/labels_retro.json')['token_same'],J('collective/data/labels_retro.json')['token_opposite']
out={s:dict(address=a) for s,a in ADDR.items()}
# Sealed S_A, read only. Hash checked against its seal.
P=R.S/'pipeline_replay_20261101/derived'
seal=json.loads((P/'interim_seal_S_A_20261101.json').read_text())
raw=(R.S/'pipeline_replay_20261101'/seal['fichier']).read_bytes()
assert hashlib.sha256(raw).hexdigest()==seal['sha256']
sa=json.loads(gzip.decompress(raw))
vus=set(sa['wallets_vus'])
for s,a in ADDR.items():
    comp=sorted((c for c in sa['comportements'] if c['wallet']==a),key=lambda c:c['premier'])
    fil=[e for e in sa['file'] if e['wallet']==a]
    out[s]['S_A']=dict(vu=a in vus,comportements=len(comp),score_max=max((c['score_max'] for c in comp),default=0),premier=time.strftime('%m-%d %H:%M',time.gmtime(comp[0]['premier'])) if comp else None,regles=comp[0]['regles'] if comp else [],priorites=len(fil))
a0=J('collective/derived/A_E1.json')['e1']['M']['a0']
g=J('collective/derived/A_E1G.json')
for s,a in ADDR.items():
    out[s]['A0']=[dict(utc=v['utc'],question=v.get('question'),outcome=v.get('outcome'),n=v['n'],u=v['u'],avant_D2=v['t']<=R.D2) for v in a0.values() if a in v['members']]
    out[s]['E1G']=[dict(utc=v['utc'],question=v.get('question'),outcome=v.get('outcome'),n=v['n']) for v in g['first_alerts'] if a in v['members']]
# E2 membership and E3.
tokens=K.by_token(fam)
burst=defaultdict(lambda:{5:0,15:0,60:0})
for tok,rs in tokens.items():
    for w in (5,15,60):
        for b in K.bursts(rs,w):
            for x in b['members']:
                if x in SLUG: burst[x][w]+=1
per=defaultdict(list)
for r in buys:
    if r[3] in SLUG: per[(r[3],r[2])].append((r[8],r[9],r[5]))
token_rows=defaultdict(list)
for r in fam: token_rows[r[2]].append(r)
for v in token_rows.values(): v.sort(key=lambda x:x[8])
for s,a in ADDR.items():
    out[s]['E2_rafales']={str(k):burst[a][k] for k in (5,15,60)}
    stl=[];best=None
    for (w,tok),v in per.items():
        if w!=a: continue
        _,dec=K.decisions(v)
        h=K.small_then_large(dec)
        if h: stl.append(dict(question=cat.get(tok,('','',''))[1],outcome=cat.get(tok,('','',''))[2],utc=time.strftime('%m-%d %H:%M',time.gmtime(h['at'])),usd=h['usd'],mediane_avant=h['median_before']))
        for ts,usd in dec:
            if not best or usd>best['usd']:
                prior=sum(r[5] for r in token_rows[tok] if ts-R.DAY<=r[8]<ts)
                before=[r for r in token_rows[tok] if r[8]<ts]
                best=dict(usd=round(usd,2),utc=time.strftime('%m-%d %H:%M',time.gmtime(ts)),question=cat.get(tok,('','',''))[1],outcome=cat.get(tok,('','',''))[2],volume_24h=round(prior,2),multiple=round(usd/prior,2) if prior else None,prix_avant=before[-1][7] if before else None)
    out[s]['E3_petits_puis_gros']=stl
    out[s]['plus_grosse_decision_taker']=best
    fs=[r for r in buys if r[3]==a and r[2]==SAME]
    tot=sum(r[5] for r in buys if r[2]==SAME)
    out[s]['mbappe_taker']=dict(usd=round(sum(r[5] for r in fs),2),part_des_achats=round(sum(r[5] for r in fs)/tot,4) if tot else None,achats_taker_total=round(tot,2))
# E5 pairs with other named wallets, within 5, 15, 60 min on one token.
pairs=defaultdict(lambda:{5:set(),15:set(),60:set()})
for tok,rs in tokens.items():
    named=[(t,w) for t,w,_ in rs if w in SLUG]
    named.sort()
    for i,(t,w) in enumerate(named):
        for t2,w2 in named[i+1:]:
            if t2-t>3600: break
            if w2!=w:
                for m in (5,15,60):
                    if t2-t<=m*60:
                        pairs[w][m].add(w2);pairs[w2][m].add(w)
for s,a in ADDR.items():
    out[s]['E5_voisins']={str(m):sorted(SLUG[x] for x in pairs[a][m]) for m in (5,15,60)}
# E4 v2.
e4=J('collective/derived/A_E4_v2.json')
for s,a in ADDR.items():
    out[s]['E4_v2_paires']=sum(1 for v in e4.values() for p in v['top'] if a in (p['a'],p['b']))
# E6 rank among comparators.
e6=J('collective/derived/B_E6.json')
comp=[e6['per_wallet'][w] for g_,ws in e6['groups'].items() if g_!='named' for w in ws]
gaps=[p['gap_s'] for p in comp if p['gap_s'] is not None]
for s,a in ADDR.items():
    p=e6['per_wallet'][a]
    out[s]['E6']=dict(premier_evenement=time.strftime('%Y-%m-%d %H:%M',time.gmtime(p['first_event'])),premier_achat_famille=time.strftime('%Y-%m-%d %H:%M',time.gmtime(p['first_family_buy'])) if p['first_family_buy'] else None,ecart_min=round(p['gap_s']/60,1) if p['gap_s'] is not None else None,comparateurs_plus_courts=sum(1 for x in gaps if p['gap_s'] is not None and x<=p['gap_s']),comparateurs=len(gaps),depots=p['deposits'],premier_retrait=time.strftime('%Y-%m-%d %H:%M',time.gmtime(p['first_withdrawal'])) if p['first_withdrawal'] else None)
e7=J('collective/derived/B_E7.json')
for s in ADDR: out[s]['E7_top20']=[dict(utc=t['utc'],usd=t['usd'],question=t['question'],outcome=t['outcome'],prix_avant=t['price_before'],paye=t['average_paid'],apres_5min=t['price_5min_after'],multiple=t['multiple_of_24h_volume']) for t in e7 if t['named']==s]
rc=J('collective/exploratoire/rank_combos.json')
combos=J('collective/exploratoire/combos.json')
TRUE=[("Kylian Mbappé finish 2nd"),("Lamine Yamal finish 3rd"),("Rodri finish 4th"),("Lionel Messi finish 5th")]
for s in ADDR:
    out[s]['rangs']=dict(quatre_avant_article=s in rc['article']['all_four_true'],quatre_avant_ceremonie=s in rc['ceremonie']['all_four_true'],trois_avant_article=s in rc['article']['three_true'])
    pw=combos['per_wallet'][s]
    tot=pw['buy_family']+pw['buy_other']
    out[s]['concentration_famille']=round(pw['buy_family']/tot,4) if tot else None
    held=[p for p in combos['outcomes'] if s in p['members']]
    out[s]['issues_avec_autres_nommes']=[dict(title=p['title'],outcome=p['outcome'],autres=[x for x in p['members'] if x!=s]) for p in held if p['wallets']>=2]
    out[s]['mbappe']=next((p['members'][s] for p in held if 'Mbappé or Lamine Yamal' in p['title'] and p['outcome']=='Mbappé'),None)
Path('collective/exploratoire/per_wallet_stats.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
for s,v in out.items():
    print(s.ljust(17),'S_A',v['S_A']['comportements'],v['S_A']['score_max'],v['S_A']['priorites'],'A0',len(v['A0']),'E1G',len(v['E1G']),'E2',v['E2_rafales'],'E3',len(v['E3_petits_puis_gros']),'E4',v['E4_v2_paires'],'E6',v['E6']['ecart_min'],v['E6']['comparateurs_plus_courts'],'/',v['E6']['comparateurs'],'E7',len(v['E7_top20']),'conc',v['concentration_famille'],'mb%',v['mbappe_taker']['part_des_achats'],'voisins5',len(v['E5_voisins']['5']))
d=J('collective/exploratoire/price_days.json')
k=d[next(x for x in d if 'Harry Kane win' in x)]
print('Kane jours',{a:(x['vwap'],x['buy'],x['named'],x['buyers']) for a,x in k.items() if '10-07'<=a<='10-13'})
