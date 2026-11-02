"""Relay par utilisateur, deux lectures refusées en 429 par cv_03, relancées lentement. Lecture seule."""
import json, time, urllib.request
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
res = {}
for name, u in (('solana_payer', '7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc'), ('brace_key', '0xc852b0938f5ad79b640d105ed11c14499454af26')):
    for attempt in range(4):
        time.sleep(40 + 40 * attempt)
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(f'https://api.relay.link/requests/v2?user={u}&limit=50', headers={'User-Agent': 'read-only'}), timeout=40))
            res[name] = r
            break
        except Exception as e:
            print(name, 'attempt', attempt, str(e)[:80], flush=True)
    res.setdefault(name, dict(_error='refused 4 times'))
(OUT / 'relay_par_utilisateur.json').write_text(json.dumps(res))
for name, v in res.items():
    q = v.get('requests')
    print(name, None if q is None else len(q), flush=True)
    for x in q or []:
        m = (x.get('data') or {}).get('metadata') or {}
        i, o = m.get('currencyIn') or {}, m.get('currencyOut') or {}
        print('  ', x.get('createdAt', '')[:19], x.get('status'), 'to', x.get('recipient'), i.get('amountFormatted'), (i.get('currency') or {}).get('symbol'), (i.get('currency') or {}).get('chainId'), '->', o.get('amountFormatted'), (o.get('currency') or {}).get('symbol'), (o.get('currency') or {}).get('chainId'))
