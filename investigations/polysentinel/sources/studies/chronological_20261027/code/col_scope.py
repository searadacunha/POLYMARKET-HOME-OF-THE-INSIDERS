"""Bounded metadata-only denominator supplement; never retroactively remaps cases."""
import argparse,gzip,hashlib,json,sqlite3
from pathlib import Path
STUDY=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--db',required=True);args=ap.parse_args()
    dest=STUDY/'data/case_key_scope_v2.json'
    if dest.exists() or (STUDY/'PROTOCOL.lock').exists():raise RuntimeError('Existing or frozen scope evidence')
    raw=(STUDY/'data/extraction_v2.json.gz').read_bytes();d=json.loads(gzip.decompress(raw))
    keys=[v['key'] for e in d['selected_events'] for v in e['case_key_inventory']]
    assert len(keys)==len(set(keys))
    with sqlite3.connect('file:'+str(Path(args.db).resolve())+'?mode=ro',uri=True) as cx:
        cx.execute('PRAGMA query_only=ON')
        total=cx.execute("SELECT count(DISTINCT key) FROM history_refs WHERE kind='case' AND observed_at<=?",(d['cutoff'],)).fetchone()[0]
    assert len(keys)<=total<=10000
    out=dict(cutoff=d['cutoff'],extraction_sha256=hashlib.sha256(raw).hexdigest(),latest_keys_examined=total,
        latest_keys_matching_selected_events=len(keys),latest_keys_outside_selected_events=total-len(keys),
        unmatched_keys_historical_event_membership_checked=False,retroactive_remapping_performed=False,
        former_membership_unknown_keys=total-len(keys),cohort_complete=False,
        limitation='Keys were selected by latest event_id at cutoff. Earlier membership of unmatched keys was not scanned; aliases/remapping may hide former event membership. No retrospective reassignment.',
        queries_requested=1,queries_returned=1,errors=0,network_requests=0,contents_decoded=0)
    dest.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('PASS: case-key scope denominator recorded; no remapping or content decoding')
if __name__=='__main__':main()
