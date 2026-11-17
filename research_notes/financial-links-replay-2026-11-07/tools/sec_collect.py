"""SEC primary records for the KPMG test: ticker->CIK (EDGAR entity search), auditor from the EX-23/EX-15 consent of
annual filings (full-text search, one query per firm), and 8-K acceptance times from data.sec.gov submissions.
Every response is archived with url and sha256. Usage: sec_collect.py OUTDIR TICKER..."""
import hashlib, json, sys, time, urllib.parse, urllib.request, pathlib
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
UA = {'user-agent': 'Polymarket-Home-of-the-Insiders forensic-research'}
FIRMS = ['KPMG', 'Ernst & Young', 'PricewaterhouseCoopers', 'Deloitte', 'BDO', 'Grant Thornton', 'Moss Adams', 'RSM US', 'Crowe']
def get(name, url):
    p = OUT / name
    if p.exists():
        return json.loads(p.read_bytes())
    for i in range(6):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read(); break
        except Exception as e:
            print('retry', url, e, flush=True); time.sleep(3 * (i + 1))
    else:
        raise SystemExit('failed ' + url)
    p.write_bytes(body)
    (OUT / (name + '.meta')).write_text(json.dumps({'url': url, 'sha256': hashlib.sha256(body).hexdigest(), 'fetched_unix': time.time()}))
    time.sleep(0.25)
    return json.loads(body)
res = {}
for t in sys.argv[2:]:
    ent = get(f'entity_{t}.json', 'https://efts.sec.gov/LATEST/search-index?' + urllib.parse.urlencode({'keysTyped': t}))
    cands = [h for h in ent['hits']['hits'] if (h['_source'].get('tickers') or '').split(', ').count(t)]
    if not cands:
        res[t] = {'cik': None}; print(t, 'NO CIK'); continue
    cik = cands[0]['_id'].zfill(10)
    hits = {}
    for f in FIRMS:
        q = {'q': f'"{f}"', 'forms': '10-K,20-F,40-F', 'ciks': cik, 'startdt': '2025-01-01', 'enddt': '2026-06-30'}
        d = get(f'fts_{t}_{f.replace(" ", "_").replace("&", "and")}.json', 'https://efts.sec.gov/LATEST/search-index?' + urllib.parse.urlencode(q))
        ex = sorted({(h['_source'].get('file_type'), h['_source'].get('file_date')) for h in d['hits']['hits']
                     if (h['_source'].get('file_type') or '').startswith(('EX-23', 'EX-15'))})
        if ex: hits[f] = ex
    sub = get(f'submissions_{cik}.json', f'https://data.sec.gov/submissions/CIK{cik}.json')
    r = sub['filings']['recent']
    k8 = [{'accession': r['accessionNumber'][i], 'acceptance': r['acceptanceDateTime'][i], 'items': r['items'][i]}
          for i in range(len(r['form'])) if r['form'][i] in ('8-K', '6-K') and '2025-09' <= r['acceptanceDateTime'][i][:7] <= '2026-04']
    res[t] = {'cik': cik, 'entity': cands[0]['_source']['entity'], 'consent_firms': hits, 'current_reports': k8}
    print(t, cik, list(hits), len(k8), flush=True)
(OUT / 'sec_summary.json').write_text(json.dumps(res, indent=1))
