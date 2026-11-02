"""Audit: what sits just before D2, and E6's truncation. Reads only."""
import json,sys,time,glob,os
from math import comb
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/collective/'
sys.path.insert(0,C+'code');sys.dont_write_bytecode=True
import rows as R
named={json.load(open(f))['address'].lower():os.path.basename(f)[:-5] for f in glob.glob('/Users/benjamindacunha/Projects/PolySentinel-investigation/cases/*.json')}
rows=[r for r in R.family() if r[0]=='M']
print('row shape',rows[0])
near=sorted((r for r in rows if r[4]=='BUY' and R.D2-3600<=r[8]<=R.D2+3600),key=lambda r:r[8])
print('D2',time.strftime('%H:%M:%S',time.gmtime(R.D2)))
big=[r for r in near if r[5]>=1000]
for r in big[:30]:print(time.strftime('%m-%d %H:%M:%S',time.gmtime(r[8])),round(r[5],2),named.get(r[3],r[3][:10]))
before=sum(r[5] for r in rows if r[4]=='BUY' and r[3] in named and r[8]<=R.D2)
print('named taker buys up to D2',round(before,2),'in the last 10 min',round(sum(r[5] for r in rows if r[4]=='BUY' and r[3] in named and R.D2-600<=r[8]<=R.D2),2))
def f(a,n1,c,n2):
    K=a+c;return sum(comb(n1,k)*comb(n2,K-k) for k in range(a,min(K,n1)+1))/comb(n1+n2,K)
print('funding under 1 h: 9/11 vs 10/43 p',round(f(9,11,10,43),5),'| vs complete histories only 10/22 p',round(f(9,11,10,22),4))
