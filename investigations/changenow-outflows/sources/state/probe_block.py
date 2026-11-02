import sys,json
sys.path.insert(0,'tools')
import es
a='0x300773969b499b9768267e0c5a049f7751de79e7'
from collections import Counter
for page in (1,2,3):
    r=es.rows('txlist',a,1,25726012,25726012,page,1000,'asc',store=False)
    print('page',page,len(r),Counter(x['blockNumber'] for x in r).most_common(3),Counter(x['from'].lower()==a for x in r), r[0]['timeStamp'] if r else '', r[0]['isError'] if r else '',r[0]['value'] if r else '',r[0]['hash'] if r else '')
    if len(r)<1000: break
r=es.rows('txlist',a,1,25726012,25726112,1,1000,'asc',store=False)
print(len(r),Counter(x['blockNumber'] for x in r).most_common(5))
