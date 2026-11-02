"""Reads only: seal check and the synchrony, placebo and review outputs of the frozen study."""
import json,hashlib,os
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/collective/'
seal=json.load(open(C+'derived/A_seal.json'))
print('seal holds',{k:hashlib.sha256(open(C+k,'rb').read()).hexdigest()==v for k,v in seal['sha256'].items()})
for f in ('derived/B_E5.json','derived/A_placebo.json','derived/B_review.json'):
    d=json.load(open(C+f)); print('==',f,list(d)[:16]); print(json.dumps(d,ensure_ascii=False)[:2100])
g=json.load(open(C+'derived/A_E1G.json')); print(list(g)); print(json.dumps({k:(v if not isinstance(v,(list,dict)) else (type(v).__name__,len(v))) for k,v in (g['D2'] if 'D2' in g else g).items()})[:800])
e=json.load(open(C+'derived/B_E6.json')); print(list(e)); print(json.dumps({k:(v if not isinstance(v,(list,dict)) else (type(v).__name__,len(v))) for k,v in e.items()})[:700])
t=[json.loads(l) for l in open(C+'registre/tests.jsonl')]
print(len(t),sorted(t[0]));
for x in t: print({k:(x.get(k) if not isinstance(x.get(k),(list,dict)) else '...') for k in ('id','nom','name','test','p','n_comparaisons','comparaisons','phase','declare','declared')})
