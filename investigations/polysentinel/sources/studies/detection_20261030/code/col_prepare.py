"""Reuse verified economic rows; discard labels and current semantic metadata."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from budget import capacity,write_bytes

STUDY = Path(__file__).resolve().parents[1]
SOURCE = STUDY.parent / 'ballon_2026_20261030/data/trades_minimal.jsonl.gz'
LOW, HIGH = 1790176669, 1792768669
FIELDS = ('id','wallet','side','timestamp','observed_at','token_id','transaction_hash',
          'order_hash','size','price','market_id','event_id','condition_id')

def sanitize(row):
    out = {k: row[k] for k in FIELDS if k in row}
    for k in ('timestamp','observed_at','size','price'):
        if type(out.get(k)) not in (int,float) or not math.isfinite(out[k]):
            raise ValueError('Invalid ' + k)
    if not (out['size'] > 0 and 0 <= out['price'] <= 1 and out['side'] in ('BUY','SELL')):
        raise ValueError('Invalid economics')
    for k in ('id','wallet','token_id','market_id','event_id','condition_id'):
        if not isinstance(out.get(k),str) or not out[k]: raise ValueError('Missing ' + k)
    return out

def main():
    out = STUDY/'data/replay_input.jsonl.gz'
    if out.exists(): raise FileExistsError(out)
    original_lock = json.loads((SOURCE.parent.parent/'PROTOCOL.lock').read_text())
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != original_lock['fichiers']['data/trades_minimal.jsonl.gz']:
        raise ValueError('Source differs from its freeze')
    counts = dict(read=0,before_window=0,after_cutoff=0,kept=0,duplicates=0)
    seen = {}
    temporary=out.with_suffix(out.suffix+'.partial')
    with gzip.open(SOURCE,'rt') as src, temporary.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as dst:
            for line in src:
                row=sanitize(json.loads(line)); counts['read']+=1
                if row['timestamp'] < LOW: counts['before_window']+=1; continue
                if row['timestamp'] >= HIGH: counts['after_cutoff']+=1; continue
                encoded=json.dumps(row,sort_keys=True,separators=(',',':'))
                capacity(len(encoded.encode())+65536)
                if row['id'] in seen:
                    if seen[row['id']] != encoded: raise ValueError('Conflicting duplicate')
                    counts['duplicates']+=1;continue
                seen[row['id']]=encoded
                dst.write((encoded+'\n').encode()); counts['kept']+=1
    assert counts['read']==sum(counts[k] for k in ('before_window','after_cutoff','kept','duplicates'))
    result=dict(counts=counts,source=str(SOURCE),source_sha256=digest,
                input_sha256=hashlib.sha256(temporary.read_bytes()).hexdigest(),fields=FIELDS,
                lower=LOW,upper_exclusive=HIGH,observed_at='unchanged actual collection timestamp',
                universe='lexically selected event family, taker-only, incomplete; NOT global universe')
    manifest=STUDY/'data/input_manifest.json'
    if manifest.exists():raise FileExistsError(manifest)
    write_bytes(manifest,(json.dumps(result,indent=2)+'\n').encode())
    temporary.rename(out)
    print(json.dumps(result))

if __name__=='__main__': main()
