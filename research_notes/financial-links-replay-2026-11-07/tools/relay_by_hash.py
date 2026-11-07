"""Resolve Relay orders by origin transaction hash (requests/v2?hash=), one call every 13 s, raw kept with sha256. Resumable.
Usage: relay_by_hash.py OUTDIR hashes.txt"""
import json, sys, time, hashlib, pathlib, urllib.request, urllib.error
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
for h in open(sys.argv[2]).read().split():
    p = OUT / f'{h}.json'
    if p.exists(): continue
    url = f'https://api.relay.link/requests/v2?hash={h}'
    for i in range(8):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent': 'forensic-replay/1.0'}), timeout=60).read(); json.loads(body); break
        except urllib.error.HTTPError as e:
            time.sleep(30 * (i + 1) if e.code == 429 else 10)
        except Exception:
            time.sleep(10)
    else:
        raise SystemExit('failed ' + h)
    p.write_bytes(body); (OUT / f'{h}.meta.json').write_text(json.dumps({'url': url, 'sha256': hashlib.sha256(body).hexdigest(), 'fetched_unix': time.time()}))
    print(h, len(json.loads(body).get('requests') or []), flush=True); time.sleep(13)
