"""Bounded public GitHub evidence; never imports or executes fetched code."""
import json, subprocess, hashlib, datetime, concurrent.futures
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPOS = ['darrnhard/polymarket-smart-money','sturzael/polymarket-edge-research','hugompt/polymarket-microstructure-lab','vsbtc/polymarket-insider-detection','bradca0/polymarket-pnl','junegun/polymarket-strategy-lab','outcometick/polymarket-backtest','SII-WANGZJ/Polymarket_data','G0BLINDEV/polymarket-backtester-realistic','Fierdimo/polymarket-analysis','tlafargue/polymarket-research']
def get(endpoint):
    r = subprocess.run(['gh','api',endpoint],capture_output=True)
    if r.returncode: raise RuntimeError(r.stderr.decode())
    return r.stdout
def one(repo):
    folder=ROOT/'data/github'/repo.replace('/','__'); folder.mkdir(exist_ok=True)
    index={'repo':repo,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[]}
    try:
        meta=json.loads(get('repos/'+repo)); index['meta']={k:meta.get(k) for k in ['default_branch','pushed_at','size','license','archived']}
        commit=json.loads(get('repos/'+repo+'/commits/'+meta['default_branch']))['sha']; index['commit']=commit
        tree=json.loads(get('repos/'+repo+'/git/trees/'+commit+'?recursive=1')); (folder/'tree.json').write_text(json.dumps(tree,indent=2))
        assert not tree.get('truncated'), 'Truncated tree'
        paths=[x for x in tree['tree'] if x['type']=='blob' and x.get('size',0)<150000]
        docs=[x for x in paths if x['path'].lower() in ['readme.md','license','license.md']]
        code=[x for x in paths if x['path'].endswith('.py') and any(k in x['path'].lower() for k in ['backtest','fee','strategy','pnl','analysis','engine']) and not Path(x['path']).name.startswith('test_')][:5]
        reports=[x for x in paths if any(k in x['path'].lower() for k in ['result','finding','report','methodolog']) and x['path'].endswith(('.md','.json','.csv'))][:3]
        import base64
        for x in {x['path']:x for x in docs+code+reports}.values():
            body=base64.b64decode(json.loads(get('repos/'+repo+'/git/blobs/'+x['sha']))['content'])
            dest=folder/'files'/x['path']; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(body)
            index['files'].append({'path':x['path'],'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
        index['status']='OK'
    except Exception as e: index.update(status='ERROR',error=str(e))
    (folder/'index.json').write_text(json.dumps(index,indent=2)); return index
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(one,REPOS))
    (ROOT/'data/github/index.json').write_text(json.dumps(rows,indent=2))
    for r in rows: print(r['repo'],r['status'],len(r['files']),r.get('error',''))
