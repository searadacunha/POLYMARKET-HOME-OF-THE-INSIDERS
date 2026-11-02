"""One-shot bounded historical extraction; no performance calculations or network.

Never run again over a frozen extraction. Each statement is an autocommit read;
observed_at<=cutoff ensures new arrivals cannot enter this historical inventory.
"""
import argparse, collections, gzip, hashlib, json, math, sqlite3, time, zlib
from datetime import datetime, timezone
from pathlib import Path

STUDY=Path(__file__).resolve().parents[1]
CUTOFF=datetime.fromisoformat('2026-10-27T21:42:00+00:00').timestamp()
COUNTS=collections.Counter()

def epoch(value):
    if not isinstance(value,str) or not value:return None
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
        return d.timestamp() if d.tzinfo else None
    except ValueError:return None

def terminal(p):
    return p.get('closed') is True or p.get('raw',{}).get('ended') is True

def official_terminal(p):
    return (p.get('verified') is True and p.get('result_available') is True
        and p.get('source_url')=='https://data-api.polymarket.com/v2/resolutions'
        and 'toutes les conditions' in p.get('proof_level','').lower())

def terminal_evidence(event_versions,milestone_versions):
    """First qualifying historical observation, never latest re-emission or first news."""
    evidence=[]
    for kind,versions in (('event',event_versions),('public_milestone',milestone_versions)):
        for v in versions:
            if not (terminal(v['payload']) if kind=='event' else official_terminal(v['payload'])):continue
            evidence.append(dict(kind=kind,observed_at=v['observed_at'],content_id=v['content_id'],
                retained_public_at=v['payload'].get('public_at'),retained_public_observed_at=v['payload'].get('public_observed_at')))
    return sorted(evidence,key=lambda v:(v['observed_at'],v['kind'],v['content_id']))

def select_case_version(key,versions,proxy):
    observable=[v for v in versions if proxy is not None and v['observed_at']<=proxy]
    eligible=[]
    for v in observable:
        t=v['payload'].get('calculated_at')
        if isinstance(t,(int,float)) and not isinstance(t,bool) and math.isfinite(t) and t<=proxy:eligible.append(v)
    reason=('no_proxy' if proxy is None else 'no_version_observable_at_proxy' if not observable
        else 'calculated_at_after_proxy_or_missing' if not eligible else None)
    selected=eligible[-1] if eligible else None
    return selected,dict(key=key,versions_total=len(versions),versions_observable_at_proxy=len(observable),
        versions_calculation_admissible=len(eligible),selected_content_id=selected['content_id'] if selected else None,exclusion_reason=reason)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--db',required=True);args=ap.parse_args()
    destination=STUDY/'data/extraction_v2.json.gz'
    if destination.exists() or (STUDY/'PROTOCOL.lock').exists():
        raise RuntimeError('Extraction already exists or protocol frozen; use a new study')
    cx=sqlite3.connect('file:'+str(Path(args.db).resolve())+'?mode=ro',uri=True,isolation_level=None)
    cx.row_factory=sqlite3.Row;cx.execute('PRAGMA query_only=ON');cx.execute('PRAGMA busy_timeout=5000')
    def query(sql,params=(),bound=None):
        COUNTS['queries_requested']+=1
        rows=cx.execute(sql,params).fetchall()
        COUNTS['queries_returned']+=1;COUNTS['rows_returned']+=len(rows)
        if not rows:COUNTS['empty_queries']+=1
        if bound is not None and len(rows)>bound:raise RuntimeError('Read bound exceeded')
        return rows
    def decode(r):
        row=query('SELECT body FROM contents WHERE id=?',(r['content_id'],))
        if len(row)!=1:raise RuntimeError('Missing referenced content')
        raw=zlib.decompress(row[0]['body'])
        if hashlib.sha256(raw).hexdigest()!=r['content_id']:raise RuntimeError('Content hash mismatch')
        COUNTS['contents_decoded']+=1
        p=json.loads(raw)
        return dict(payload=p,content_id=r['content_id'],observed_at=r['observed_at'],key=r['key'])
    def latest(kind,t,bound):
        return query('''SELECT key,content_id,observed_at FROM (SELECT *,ROW_NUMBER() OVER
          (PARTITION BY key ORDER BY observed_at DESC,id DESC) n FROM history_refs
          WHERE kind=? AND observed_at<=?) WHERE n=1 ORDER BY key LIMIT ?''',(kind,t,bound+1),bound)
    def versions(kind,key,t,bound):
        return query('SELECT key,content_id,observed_at FROM history_refs WHERE kind=? AND key=? AND observed_at<=? ORDER BY observed_at,id LIMIT ?',
                     (kind,str(key),t,bound+1),bound)
    def at(kind,key,t):
        r=query('SELECT key,content_id,observed_at FROM history_refs WHERE kind=? AND key=? AND observed_at<=? ORDER BY observed_at DESC,id DESC LIMIT 1',(kind,str(key),t))
        COUNTS['point_requests']+=1;COUNTS['point_received' if r else 'point_missing']+=1
        return decode(r[0]) if r else None
    cycle_rows=query('SELECT id,start,end,status FROM cycles WHERE end IS NOT NULL AND end<=? ORDER BY end',(CUTOFF,),10000)
    cycles=[c for c in cycle_rows if c['status'] in ('ok','degraded')]
    if not cycles:raise RuntimeError('No completed cycle')
    cutoff=cycles[-1]['end'];start=query('SELECT MIN(start) first FROM cycles WHERE start<=?',(cutoff,))[0]['first'];lower=cutoff-86400
    public={r['key']:decode(r) for r in latest('public_milestone',cutoff,1000)}
    inventory=[];selected=[];catalogue_count=0;exclusions=collections.Counter()
    for r in latest('event',cutoff,10000):
        catalogue_count+=1;e=decode(r);p=e['payload'];eid=str(p['id']);end=epoch(p.get('end_date'))
        pm=public.get(eid,{}).get('payload',{})
        official=official_terminal(pm)
        reason=None
        if eid=='606422' or 'fed decision' in p.get('title','').lower():reason='known_fomc_excluded'
        elif not(terminal(p) or official):reason='no_explicit_terminal_marker'
        elif end is None:reason='missing_dated_end'
        elif not lower<=end<=cutoff:reason='outside_24h_end_window'
        if reason:
            exclusions[reason]+=1;continue
        inventory.append(dict(event=e,scheduled_end=end,public_milestone=public.get(eid)))
    inventory.sort(key=lambda r:(r['scheduled_end'],str(r['event']['payload']['id'])))
    selected=inventory[:8];exclusions['beyond_eight_bound']=max(0,len(inventory)-8)
    candidate_inventory=[dict(id=r['event']['payload']['id'],title=r['event']['payload']['title'],scheduled_end=r['scheduled_end'],selected=i<8) for i,r in enumerate(inventory)]
    selected_ids={str(e['event']['payload']['id']) for e in selected}
    case_keys=collections.defaultdict(list)
    for r in latest('case',cutoff,10000):
        d=decode(r);eid=str(d['payload'].get('event_id'))
        if eid in selected_ids:case_keys[eid].append(r['key'])
    all_versions=0;trade_queries=0
    for ev in selected:
        eid=str(ev['event']['payload']['id']);slug=ev['event']['payload'].get('slug')
        evversions=[decode(r) for r in versions('event',eid,cutoff,10000)]
        milestone_versions=[decode(r) for r in versions('public_milestone',eid,cutoff,1000)]
        terminal_refs=terminal_evidence(evversions,milestone_versions)
        if not terminal_refs:raise RuntimeError('Selected terminal event without qualifying terminal history')
        first_terminal=terminal_refs[0]['observed_at'];before=[c for c in cycles if c['end']<first_terminal]
        proxy=before[-1]['end'] if before else None
        ev.update(first_event_observed_at=min(v['observed_at'] for v in evversions),first_terminal_observed_at=first_terminal,
                  event_versions=evversions,public_milestone_versions=milestone_versions,terminal_evidence=terminal_refs,
                  proxy_cycle_end=proxy,proxy_cycle_id=before[-1]['id'] if before else None,cases=[],case_key_inventory=[],
                  cohort_complete=False,cohort_completeness_reason='Only emitted dossier population retained; exhaustive eligible cohort was not archived',
                  authoritative_target=None,source_url='https://polymarket.com/event/'+str(slug))
        for key in sorted(case_keys[eid]):
            vr=versions('case',key,cutoff,30000);all_versions+=len(vr)
            if all_versions>30000:raise RuntimeError('Total case-version bound exceeded')
            ds=[decode(r) for r in vr]
            d,selection=select_case_version(key,ds,proxy)
            ev['case_key_inventory'].append(selection)
            if d is None:continue
            p=d['payload'];t=p['calculated_at'];proofs=[]
            if not isinstance(t,(int,float)):raise ValueError('Case calculation time missing')
            for alert in p.get('alerts',[]):
                trades=[]
                for tid in alert.get('trade_ids',[]):
                    trade_queries+=1
                    if trade_queries>5000:raise RuntimeError('Alert-trade query bound exceeded')
                    trades.append(at('trade',tid,t))
                proofs.append(dict(alert=alert,trades=trades,market=at('market',alert.get('market_id'),t)))
            d.update(alert_proofs=proofs,event_at_calculation=at('event',eid,t),
                     first_case_observed_at=min(x['observed_at'] for x in ds),history_versions_available=len(ds))
            ev['cases'].append(d)
        excluded=collections.Counter(v['exclusion_reason'] for v in ev['case_key_inventory'] if v['exclusion_reason'])
        ev['case_key_counts']=dict(examined=len(ev['case_key_inventory']),retained=len(ev['cases']),
            excluded=sum(excluded.values()),exclusions=dict(excluded))
        if ev['case_key_counts']['examined']!=ev['case_key_counts']['retained']+ev['case_key_counts']['excluded']:
            raise RuntimeError('Case-key reconciliation failed')
        # Activities are selected by known wallets, then filtered by event; no future receipt imported.
        activities=[]
        for w in sorted({d['payload']['wallet'] for d in ev['cases']}):
            refs=query('SELECT key,content_id,observed_at FROM history_refs WHERE kind=? AND key LIKE ? AND observed_at<=? ORDER BY observed_at,id LIMIT 5001',
                       ('wallet_activity',w+':%',cutoff),5000)
            for r in refs:
                d=decode(r);row=d['payload'].get('row',{})
                if row.get('event_slug')==slug:activities.append(d)
            if len(activities)>5000:raise RuntimeError('Activity bound exceeded')
        ev['activities']=activities
        ev['resolution_records']=[]
    # Only 222 condition records at preparation; refuse unexpected unbounded growth.
    for r in latest('public_condition',cutoff,5000):
        d=decode(r);eid=str(d['payload'].get('event_id'))
        if eid in selected_ids:
            ev=next(e for e in selected if str(e['event']['payload']['id'])==eid)
            d['resolution_payload']=at('resolution',r['key'],cutoff)
            ev['resolution_records'].append(d)
    out=dict(schema_version=2,cutoff_requested=CUTOFF,cutoff=cutoff,cutoff_cycle_id=cycles[-1]['id'],
             bot_first_cycle_start=start,source='SQLite history_refs/contents; read-only, no network',
             extraction_started_plan_sha256=hashlib.sha256((STUDY/'analysis_plan.md').read_bytes()).hexdigest(),
             catalogue_events=catalogue_count,exclusions=dict(exclusions),candidate_inventory=candidate_inventory,
             cycle_status_counts=dict(collections.Counter(c['status'] for c in cycle_rows)),completed_cycle_count=len(cycles),
             selected_events=selected,counts=dict(COUNTS),completed_at=time.time(),case_versions_decoded=all_versions)
    raw=json.dumps(out,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode()
    compressed=gzip.compress(raw,mtime=0)
    if len(compressed)>15_000_000:raise RuntimeError('Extraction exceeds 15 MB sub-budget')
    destination.write_bytes(compressed)
    (STUDY/'data/collection_validation_v2.json').write_text(json.dumps(dict(sha256=hashlib.sha256(compressed).hexdigest(),
        bytes=len(compressed),uncompressed_bytes=len(raw),source_cutoff=cutoff,counts=dict(COUNTS),
        error_count=0,rate_limited=0,network_requests=0,selected_events=len(selected),plan_sha256=out['extraction_started_plan_sha256']),indent=2)+'\n')
    cx.close()
    print(json.dumps(dict(extraction='data/extraction_v2.json.gz',bytes=len(compressed),selected_events=len(selected),counts=dict(COUNTS))))

if __name__=='__main__':main()
