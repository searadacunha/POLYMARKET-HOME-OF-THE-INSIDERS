import json,sys,collections; sys.path.insert(0,'.')
import chainlib as c, tokens
name,root,chain=sys.argv[1],sys.argv[2],int(sys.argv[3])
r=json.load(open(f'../state/runs/{name}.json'))
N=r['nodes']; E=[e for e in r['edges'] if tokens.worth_following(chain,e)]
out=collections.defaultdict(list)
for e in E: out[e['src']].append(e)
seen=set()
def lab(a):
    n=N.get(a,{}); l=[x['name'] for x in n.get('labels',[])][:2]
    return f"{a[:10]}…{a[-4:]}"+(f" {l}" if l else '')+(f" [{n.get('stop')}]" if n.get('stop') else '')+(f" nonce={n.get('nonce')}" if n.get('nonce',0)>3 else '')
def show(a,d):
    if a in seen or d>int(sys.argv[4]): return
    seen.add(a)
    rows=sorted(out[a],key=lambda e:e['ts'])
    if len(rows)>18: 
        ag=collections.defaultdict(lambda:[0,0.0,None,None])
        for e in rows:
            g=ag[(e['dst'],tokens.canonical_symbol(chain,e))]; g[0]+=1; g[1]+=c.amount(e); g[2]=g[2] or e['ts']; g[3]=e['ts']
        for (dst,s),g in sorted(ag.items(),key=lambda kv:-kv[1][1])[:14]:
            print('  '*d,f"→ {g[0]}x {g[1]:,.4f} {s} {c.utc(g[2])[5:16]} … {c.utc(g[3])[5:16]} {lab(dst)}")
            show(dst,d+1)
        return
    for e in rows:
        print('  '*d,f"→ {c.amount(e):,.4f} {tokens.canonical_symbol(chain,e)} {c.utc(e['ts'])[5:19]} {e['tx'][:12]} {lab(e['dst'])}")
        show(e['dst'],d+1)
print(lab(root)); show(root,1)
