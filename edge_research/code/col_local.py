"""Stream a fixed byte prefix; retain quotes and full books without changing live files."""
import json, hashlib, gzip, collections, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/benjamindacunha/phi-live/market.jsonl')
def extract():
    for name in ('quotes.jsonl.gz','books.jsonl.gz','local_manifest.json'):
        if (ROOT/'data'/name).exists(): raise FileExistsError('Preserve existing extraction: '+name)
    size=SOURCE.stat().st_size; digest=hashlib.sha256(); counts=collections.Counter(); pending={}; last_t={}
    start=datetime.datetime(2026,11,14,tzinfo=datetime.timezone.utc).timestamp()
    end=datetime.datetime(2026,11,16,13,tzinfo=datetime.timezone.utc).timestamp()
    def emit(row,fh): fh.write(json.dumps(row,separators=(',',':'))+'\n')
    with SOURCE.open('rb') as src,gzip.open(ROOT/'data/quotes.jsonl.gz','wt') as quotes,gzip.open(ROOT/'data/books.jsonl.gz','wt') as books:
        while src.tell()<size:
            b=src.readline(min(2000000,size-src.tell())); digest.update(b)
            if not b.endswith(b'\n'):
                if src.tell()==size: counts['partial_tail']+=1; break
                raise ValueError('oversize line')
            r=json.loads(b); counts['rows']+=1; counts['type_'+str(r.get('event_type'))]+=1
            t=r.get('received'); asset=r.get('asset_id')
            if t is None or not start<=t<end: counts['outside_window']+=1; continue
            if not asset: counts['no_asset']+=1; continue
            if t<last_t.get(asset,0): counts['backwards']+=1; continue
            last_t[asset]=t
            if r.get('event_type')=='book' and 'bids' in r and 'asks' in r:
                emit(r,books); counts['full_books']+=1
                bid=max((float(x['price']) for x in r['bids']),default=None)
                ask=min((float(x['price']) for x in r['asks']),default=None)
            else: bid=r.get('best_bid'); ask=r.get('best_ask')
            if bid is None or ask is None: counts['no_bbo']+=1; continue
            bid,ask=float(bid),float(ask)
            if not 0<bid<=ask<1: counts['invalid_bbo']+=1; continue
            row=[asset,t,bid,ask,r.get('market'),r.get('timestamp')]
            prev=pending.get(asset)
            if prev is not None and int(prev[1])!=int(t): emit(prev,quotes); counts['quotes']+=1
            if prev is not None and int(prev[1])==int(t): counts['within_second_replacements']+=1
            pending[asset]=row
        for row in pending.values(): emit(row,quotes); counts['quotes']+=1
    manifest={'source':str(SOURCE),'prefix_bytes':size,'prefix_sha256':digest.hexdigest(),'window':[start,end],'counts':dict(counts)}
    (ROOT/'data/local_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps(manifest,indent=2))
if __name__=='__main__': extract()
