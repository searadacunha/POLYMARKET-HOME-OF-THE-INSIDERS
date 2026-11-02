import json,collections,statistics as st,datetime as dt,math,sys
T='0x3b6dcfde35e53fb7dca8571f23286631b5123c5b'
OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'USDC','0xdac17f958d2ee523a2206206994597c13d831ec7':'USDT'}
P={'4a9a':('0x4a9a16755a6bf64291cd2c9eb027b39c129ff58d','stable'),'b715':('0xb7152d5900da932b7fc3cac97aebfc815f88d5ca','stable'),
   'b93e':('0xb93e3d70ac9cacd51764f09ae0d01b905dc291e1','stable'),'26c5':('0x26c50e673fca05131c9b9f23d213b977d9a34c77','stable'),
   '9744':('0x974413b8c1d9eeb96758f9d4b5093ea12b3eef54','eth'),'9bdb':('0x9bdbbd6ff7889e1cb668c21c5da3c8a73a7742ae','eth')}
if len(sys.argv)>1: P={k:v for k,v in P.items() if k in sys.argv[1:]}
def pct(v,q): 
    i=min(len(v)-1,max(0,int(round(q*(len(v)-1))))); return v[i]
def d(ts): return dt.datetime.fromtimestamp(ts,dt.UTC)
out={}
for k,(a,kind) in P.items():
    if kind=='stable':
        rows=json.load(open(f'deep_{a[:10]}_1_tokentx.json'))
        pay=[(int(x['timeStamp']),int(x['blockNumber']),x['to'].lower(),int(x['value'])/1e6,OFF[x['contractAddress'].lower()],x['hash']) for x in rows if x['from'].lower()==a and x['contractAddress'].lower() in OFF and int(x['value'])>=10**6]
        ref=[(int(x['timeStamp']),int(x['value'])/1e6) for x in rows if x['to'].lower()==a and x['from'].lower()==T and x['contractAddress'].lower() in OFF]
        unit='$'
    else:
        rows=json.load(open(f'deep_{a[:10]}_1_txlist.json'))
        pay=[(int(x['timeStamp']),int(x['blockNumber']),x['to'].lower(),int(x['value'])/1e18,'ETH',x['hash']) for x in rows if x['from'].lower()==a and int(x['value'])>0 and x.get('isError')!='1']
        ref=[(int(x['timeStamp']),int(x['value'])/1e18) for x in rows if x['to'].lower()==a and x['from'].lower()==T and x.get('isError')!='1']
        unit='ETH'
    pay.sort(); ref.sort()
    v=sorted(p[3] for p in pay); n=len(v)
    days=collections.Counter(d(p[0]).date() for p in pay)
    hours=collections.Counter(d(p[0]).hour for p in pay); wd=collections.Counter(d(p[0]).weekday() for p in pay)
    blk=collections.Counter(p[1] for p in pay); sameblock=sum(c for c in blk.values() if c>1)/n
    gaps=[pay[i][0]-pay[i-1][0] for i in range(1,n)]
    rec=collections.Counter(p[2] for p in pay)
    amt=collections.Counter(round(p[3],2 if kind=='stable' else 4) for p in pay)
    top20=sum(c for _,c in amt.most_common(20))/n
    integer=sum(1 for x in v if abs(x-round(x))<1e-9)/n if kind=='stable' else sum(1 for x in v if abs(x*100-round(x*100))<1e-9)/n
    twodec=sum(1 for x in v if abs(x*100-round(x*100))<1e-6)/n
    mult10=sum(1 for x in v if abs(x/10-round(x/10))<1e-9)/n
    rv=sorted(r[1] for r in ref); rgaps=[ref[i][0]-ref[i-1][0] for i in range(1,len(ref))]
    tok=collections.Counter(p[4] for p in pay)
    peak=hours.most_common(1)[0][0]; low=min(range(24),key=lambda h:hours[h])
    out[k]={'address':a,'kind':kind,'unit':unit,'first_payout':str(d(pay[0][0])),'last_payout':str(d(pay[-1][0])),
      'lifetime_days':round((pay[-1][0]-pay[0][0])/86400,1),'active_days':len(days),'payouts':n,'beneficiaries':len(rec),
      'repeat_beneficiaries':sum(1 for c in rec.values() if c>=2),'repeat_share':round(sum(1 for c in rec.values() if c>=2)/len(rec),4),
      'total':round(sum(v),2),'mean':round(sum(v)/n,4),'median':round(st.median(v),4),
      'p10':pct(v,.1),'p25':pct(v,.25),'p75':pct(v,.75),'p90':pct(v,.9),'p99':pct(v,.99),'max':v[-1],
      'per_day_median':st.median(days.values()),'per_day_mean':round(n/len(days),1),'gap_median_s':st.median(gaps),
      'same_block_share':round(sameblock,4),'integer_share':round(integer,4),'twodec_share':round(twodec,4),'mult10_share':round(mult10,4),
      'top20_amounts_share':round(top20,4),'top_amounts':amt.most_common(10),'tokens':dict(tok),
      'hour_share':{h:round(hours[h]/n,4) for h in range(24)},'peak_hour_utc':peak,'low_hour_utc':low,
      'weekday_share':{w:round(wd[w]/n,4) for w in range(7)},
      'refills':len(ref),'first_refill':str(d(ref[0][0])) if ref else None,'last_refill':str(d(ref[-1][0])) if ref else None,
      'refill_median':st.median(rv) if rv else None,'refill_mean':round(sum(rv)/len(rv),2) if rv else None,'refill_top':collections.Counter(round(x) for x in rv).most_common(5),
      'refill_gap_median_min':round(st.median(rgaps)/60,1) if rgaps else None}
    o=out[k]
    print(f"{k} {kind} payouts {n} benef {len(rec)} rep {o['repeat_share']} total {o['total']:,} med {o['median']} mean {o['mean']} p10 {o['p10']} p90 {o['p90']} p99 {o['p99']} | /day med {o['per_day_median']} | sameblock {o['same_block_share']} | int {o['integer_share']} 2dec {o['twodec_share']} top20 {o['top20_amounts_share']} | peak {peak}h low {low}h | refills {len(ref)} med {o['refill_median']} gap {o['refill_gap_median_min']}min top {o['refill_top'][:3]} | {o['first_payout'][:10]}→{o['last_payout'][:10]}")
fn='p5_fingerprint.json' if len(sys.argv)==1 else 'p5_fingerprint_'+'_'.join(sys.argv[1:])+'.json'
json.dump(out,open(fn,'w'),default=str)
