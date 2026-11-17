"""Resolve exact Polymarket profile names to proxy wallets via gamma public-search; keeps every raw response."""
import json, sys, time, urllib.request, urllib.parse, pathlib
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
names = sys.argv[2:]
res = {}
for n in names:
    url = 'https://gamma-api.polymarket.com/public-search?' + urllib.parse.urlencode({'q': n, 'search_profiles': 'true', 'limit_per_type': 50})
    raw = urllib.request.urlopen(urllib.request.Request(url, headers={'user-agent': 'forensic-replay/1.0'}), timeout=30).read()
    (OUT / f'search_{n}.json').write_bytes(raw)
    profs = json.loads(raw).get('profiles') or []
    exact = [p for p in profs if (p.get('name') or '') == n]
    ci = [p for p in profs if (p.get('name') or '').lower() == n.lower()]
    res[n] = {'exact': [p['proxyWallet'] for p in exact], 'case_insensitive': [(p['name'], p['proxyWallet']) for p in ci], 'url': url}
    print(n, res[n]['exact'], res[n]['case_insensitive'])
    time.sleep(0.4)
(OUT / 'resolution.json').write_text(json.dumps(res, indent=1))
