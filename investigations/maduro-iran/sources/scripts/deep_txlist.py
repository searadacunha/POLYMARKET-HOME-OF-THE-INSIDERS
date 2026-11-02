import sys,json,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from deep_evm import pull
for a in sys.argv[1:]:
    a=a.lower()
    for act in ('txlist','tokentx'):
        rows,trunc=pull(1,act,a,maxcalls=900)
        json.dump(rows,open(f'deep_{a[:10]}_1_{act}.json','w'))
        print(a[:10],act,len(rows),'truncated' if trunc else '',flush=True)
