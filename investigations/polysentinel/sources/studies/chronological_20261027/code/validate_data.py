"""Validate the extracted raw contract without calculating outcome rates."""
import gzip,hashlib,json
from pathlib import Path

STUDY=Path(__file__).resolve().parents[1]
def main():
    path=STUDY/'data/extraction_v2.json.gz';d=json.loads(gzip.decompress(path.read_bytes()))
    cv=json.loads((STUDY/'data/collection_validation_v2.json').read_text())
    scope=json.loads((STUDY/'data/case_key_scope_v2.json').read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest()==cv['sha256']
    assert scope['extraction_sha256']==cv['sha256'] and scope['cutoff']==d['cutoff']
    assert scope['latest_keys_examined']==scope['latest_keys_matching_selected_events']+scope['latest_keys_outside_selected_events']
    assert scope['latest_keys_matching_selected_events']==sum(len(e['case_key_inventory']) for e in d['selected_events'])
    assert cv['error_count']==0 and cv['network_requests']==0
    assert d['cutoff']<=d['cutoff_requested']
    events=d['selected_events'];assert len(events)<=8
    order=[(e['scheduled_end'],str(e['event']['payload']['id'])) for e in events]
    assert order==sorted(order) and len({e['event']['payload']['id'] for e in events})==len(events)
    def references(x):
        if isinstance(x,dict):
            if {'payload','observed_at','content_id','key'}<=x.keys():
                assert x['observed_at']<=d['cutoff']
                assert len(x['content_id'])==64
            for v in x.values():references(v)
        elif isinstance(x,list):
            for v in x:references(v)
    references(d)
    for e in events:
        assert d['cutoff']-86400<=e['scheduled_end']<=d['cutoff']
        assert str(e['event']['payload']['id'])!='606422'
        assert 'fed decision' not in e['event']['payload']['title'].lower()
        assert any(v['payload'].get('closed') is True or v['payload'].get('raw',{}).get('ended') is True for v in e['event_versions']) or e['public_milestone']
        if e['proxy_cycle_end'] is not None:assert e['proxy_cycle_end']<e['first_terminal_observed_at']
        assert e['first_terminal_observed_at']==min(v['observed_at'] for v in e['terminal_evidence'])
        counts=e['case_key_counts'];assert counts['examined']==counts['retained']+counts['excluded']
        assert counts['retained']==len(e['cases']) and counts['examined']==len(e['case_key_inventory'])
        assert counts['excluded']==sum(counts['exclusions'].values())
        for r in e['cases']:
            assert r['observed_at']<=e['proxy_cycle_end']
            assert r['payload']['calculated_at']<=e['proxy_cycle_end']
    assert sum(p.stat().st_size for p in STUDY.rglob('*') if p.is_file())<25_000_000
    print('PASS: bounded sorted population; SHA content extraction; reference cutoffs; PIT case harvest; no network; artifact budget')

if __name__=='__main__':main()
