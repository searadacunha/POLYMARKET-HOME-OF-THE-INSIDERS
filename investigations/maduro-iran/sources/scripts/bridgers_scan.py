import sys,json,datetime as dt; sys.path.insert(0,'.')
from common import *
TOP='0x45f377f845e1cc76ae2c08f990e15d58bcb732db46f92a4852b956580c3a162f'
def blk(chain,t,c): return int(es(chain,module='block',action='getblocknobytime',timestamp=t,closest=c))
def decode(lg):
    d=lg['data'][2:]; w=[d[i:i+64] for i in range(0,len(d),64)]
    tok='0x'+w[0][24:]; sender='0x'+w[2][24:]; fromAmt=int(w[4],16); minRet=int(w[5],16)
    # strings: offsets w[1], w[3]
    def s(off):
        o=int(off,16)//32; n=int(w[o],16); return bytes.fromhex(''.join(w[o+1:o+1+(n+31)//32]))[:n].decode('ascii','ignore')
    return dict(token=tok,sender=sender,fromAmt=fromAmt,minRet=minRet,toTok=s(w[1]),dest=s(w[3]),tx=lg['transactionHash'],ts=int(lg['timeStamp'],16))
def scan(chain,contract,t0,t1):
    b0=blk(chain,t0,'before'); b1=blk(chain,t1,'after'); out=[]; start=b0
    while start<=b1:
        r=es(chain,module='logs',action='getLogs',address=contract,topic0=TOP,fromBlock=start,toBlock=b1,page=1,offset=1000)
        for lg in r:
            try: out.append(decode(lg))
            except Exception as e: pass
        if len(r)<1000: break
        start=int(r[-1]['blockNumber'],16)+1
    return out
if __name__=='__main__':
    chain=int(sys.argv[1]); c=sys.argv[2]; t0=int(sys.argv[3]); t1=int(sys.argv[4]); flt=sys.argv[5:] 
    ev=scan(chain,c,t0,t1)
    print('events',len(ev))
    for e in ev:
        if not flt or any(f in e['dest'] or f.lower()==e['sender'] for f in flt):
            print(dt.datetime.fromtimestamp(e['ts'],dt.UTC).strftime('%m-%d %H:%M:%S'), e['sender'], e['token'][:10], e['fromAmt'], '->', e['toTok'], e['dest'], 'minRet',e['minRet'], e['tx'])
