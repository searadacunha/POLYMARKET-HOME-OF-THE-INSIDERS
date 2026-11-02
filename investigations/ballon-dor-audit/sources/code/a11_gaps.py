"""Audit: when two dossiers used the same shared address, how close in time and amount, against what that address's traffic would give by chance. Plus chronology of the seal. Reads only."""
import glob,itertools,json,math,os,time
from collections import defaultdict
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
nodes=json.load(open(I+'graphs/links_classified.json'))['nodes']
U=lambda t:time.strftime('%m-%d %H:%M:%S',time.gmtime(t)) if t else None
for n in nodes:
    a=n['address'];al=a.lower()
    by=defaultdict(list)
    for r in rel:
        if (r['source'] or '').lower()==al or (r['target'] or '').lower()==al:
            by[r['case']].append(r)
    print('\n',a[:12],n['class_'],'relations',sum(len(v) for v in by.values()))
    best=[]
    for c1,c2 in itertools.combinations(sorted(by),2):
        for x in by[c1]:
            for y in by[c2]:
                if x['at'] and y['at']:
                    best.append((abs(x['at']-y['at']),c1,c2,U(x['at']),x['amount'],y['amount'],x['chain'],y['chain'],'in' if (x['target'] or '').lower()==al else 'out','in' if (y['target'] or '').lower()==al else 'out'))
    for b in sorted(best,key=lambda z:z[0])[:4]:print('   gap',round(b[0]/60,1),'min',b[1:])
print('\n=== seal chronology')
import glob
seal=json.load(open(I+'collective/derived/A_seal.json'))['sealed_at'];print('A sealed',U(seal))
lock=I+'collective/PROTOCOL.lock'
print('lock mtime',U(os.path.getmtime(lock)))
f=glob.glob(os.path.expanduser('~/.claude/projects/*/fc0d86a8*.jsonl'))[0]
first={}
want=('brace227','Thin-Disclaimer-Life','OuldLm3alem')
with open(f,errors='ignore') as fh:
    for line in fh:
        d=json.loads(line) if line.strip() else {}
        ts=d.get('timestamp')
        for w in want:
            if w not in first and w in line and ts: first[w]=(ts,d.get('type'))
print('first mention in the session transcript',first)
