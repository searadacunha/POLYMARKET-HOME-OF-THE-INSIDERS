"""Independent synthetic model; no study import, real input or disk writes."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import random

BASE=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')

def active(g, cutoff):
    return g['side']=='BUY' and g['nominal']>=250 and g['at']>=cutoff

def synchrony(groups, cutoff):
    # Enumerate all windows ending at each group, independently of a sliding pointer.
    ordered=sorted((g for g in groups if active(g,cutoff)),key=lambda g:(g['at'],g['id']))
    found={}
    for i,end in enumerate(ordered):
        batch=[g for g in ordered[:i+1] if g['key']==end['key'] and end['at']-90<=g['at']]
        owners=defaultdict(set)
        for g in batch:
            for tx in g['tx']:owners[tx].add(g['wallet'])
        unique={tx:next(iter(ws)) for tx,ws in owners.items() if len(ws)==1}
        wallets=set(unique.values())
        if len(wallets)>=3:
            detail=(tuple(sorted(wallets)),tuple(sorted(unique)),batch[0]['at'],end['at'])
            for g in batch:
                if g['wallet'] in wallets:found[g['id']]=detail
    return found

def rows_by_wallet(groups):
    result=defaultdict(list)
    for g in groups:result[g['wallet']].append(g)
    return result

def update(old,new,previous_cutoff,cutoff):
    old_by=rows_by_wallet(old); new_by=rows_by_wallet(new)
    changed={w for w in old_by.keys()|new_by.keys() if old_by[w]!=new_by[w]}
    affected=changed|{w for w,gs in new_by.items() if any(previous_cutoff<=g['at']<cutoff for g in gs)}
    eligible=[g for g in new if active(g,cutoff)]
    def neighbors(gs):
        return {h['wallet'] for g in gs if g['side']=='BUY' and g['nominal']>=250
                for h in eligible if g['key']==h['key'] and abs(g['at']-h['at'])<=90}
    for w in tuple(affected):affected |= neighbors(old_by[w]+new_by[w])
    targets=affected&new_by.keys()
    included=set(targets)
    for w in targets:included |= neighbors(g for g in new_by[w] if g['at']>=cutoff)
    previous=synchrony(old,previous_cutoff)
    fresh=synchrony([g for g in new if g['wallet'] in included],cutoff)
    owners={g['id']:g['wallet'] for g in new}
    combined={gid:v for gid,v in previous.items() if gid in owners and owners[gid] not in targets}
    combined.update({gid:v for gid,v in fresh.items() if owners[gid] in targets})
    return combined

failures=[]
cache_comparisons=0
for seed in range(240):
    rng=random.Random(50000+seed)
    old=[]
    for i in range(48):
        old.append(dict(id=f'g{i:03}',wallet=f'w{rng.randrange(12):02}',key=rng.randrange(2),
            at=rng.choice([0,30,60,90,120,150,180,210,240,270,300,330,360,390,420,450,480,510,540,570,600]),
            nominal=rng.choice([249,250,300,1000]),side=rng.choice(['BUY','BUY','BUY','SELL']),
            tx=[f'shared-{i//4}' if i%7==0 else f'tx-{i}']))
    new=[dict(g,tx=list(g['tx'])) for g in old]
    i=rng.randrange(len(new)); mode=seed%6
    if mode==0:new.pop(i)
    elif mode==1:new[i]['at']+=rng.choice([-90,-60,60,90])
    elif mode==2:new[i]['nominal']=249 if new[i]['nominal']>=250 else 300
    elif mode==3:new.append(dict(id='added',wallet='new-wallet',key=rng.randrange(2),at=570,nominal=300,side='BUY',tx=['new-tx']))
    elif mode==4:
        victim=new[i]['wallet']; new=[g for g in new if g['wallet']!=victim]
    else:new[i]['tx']=['shared-0']
    old_cutoff=rng.choice([0,120,240]); new_cutoff=old_cutoff+(60 if seed%2 else 0)
    got=update(old,new,old_cutoff,new_cutoff); wanted=synchrony(new,new_cutoff)
    cache_comparisons+=1
    if got!=wanted:failures.append(dict(test='cache-neighborhood-model',seed=seed))

calendar_comparisons=0
for horizon in (3600,4200):
    for window in (120,600):
        for delay in (0,60,300,900):
            rng=random.Random(horizon+window+delay)
            rows=[dict(at=rng.randrange(horizon),wallet=f'w{rng.randrange(4)}',event=f'e{rng.randrange(2)}',side=rng.choice(['BUY','BUY','SELL'])) for _ in range(24)]
            def count(t):
                return len({(r['wallet'],r['event']) for r in rows if r['at']+delay<=t and r['at']>=t-window and r['side']=='BUY'})
            dense=sum(count(t) for t in range(0,horizon,60))
            sparse={0,horizon-60}
            for r in rows:
                for t in (math.ceil((r['at']+delay)/60)*60,(math.floor((r['at']+window)/60)+1)*60):
                    if 0<=t<horizon:sparse.add(t)
            sparse=sorted(sparse)
            weighted=sum(count(t)*((sparse[i+1]-t)//60 if i+1<len(sparse) else 1) for i,t in enumerate(sparse))
            calendar_comparisons+=1
            if weighted!=dense:failures.append(dict(test='calendar-model',horizon=horizon,window=window,delay=delay,dense=dense,weighted=weighted))

hash_checks={}
for report in ('replay_fast_controls_v3.json','replay_synthetic_controls_v3.json'):
    for rel,expected in json.loads((BASE/'controles'/report).read_text())['hashes'].items():
        hash_checks[rel]=hashlib.sha256((BASE/'code'/rel).read_bytes()).hexdigest()==expected
print(json.dumps(dict(status='PASS' if not failures and all(hash_checks.values()) else 'FAIL',
    dataset='synthetic-only-independent-model',cache_dependency_comparisons=cache_comparisons,
    weighted_calendar_comparisons=calendar_comparisons,total_synthetic_comparisons=cache_comparisons+calendar_comparisons,
    failures=failures,control_report_hash_checks=hash_checks,
    scope='Dependency closure and calendar algebra only; does not execute WalletCache or any study module.'),indent=2))
