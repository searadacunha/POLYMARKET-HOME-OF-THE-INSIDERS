"""Match Relay withdrawals of one Polymarket account to Relay deposits of another through the same intermediary wallet.
Input: raw Relay pages (collect.py layout RAW/relay/<addr>/pNNN.json). Output: JSON list of candidate handoffs with both
request ids, in/out tx hashes and amounts as reported by Relay. Chain receipts are checked separately."""
import json, glob, sys, pathlib, datetime
RAW = pathlib.Path(sys.argv[1]); accts = json.load(open(sys.argv[2]))  # {name: proxy}
byp = {v.lower(): k for k, v in accts.items()}
reqs = {}
for f in glob.glob(str(RAW / 'relay' / '*' / 'p[0-9][0-9][0-9].json')):
    for q in json.load(open(f)).get('requests') or []:
        reqs[q['id']] = q
def norm(a): return a.lower() if a and a.startswith('0x') else a
def amt(q, side):
    m = (q.get('data') or {}).get('metadata') or {}
    x = m.get('currencyIn' if side == 'in' else 'currencyOut') or {}
    return x.get('amountFormatted'), (x.get('currency') or {}).get('symbol'), (x.get('currency') or {}).get('chainId')
def ts(s): return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
W, D = [], []  # withdrawals (account -> X), deposits (X -> account)
for q in reqs.values():
    u, r = norm(q.get('user')), norm(q.get('recipient'))
    if u in byp and r not in byp and q.get('status') == 'success': W.append(q)
    if r in byp and u not in byp and q.get('status') == 'success': D.append(q)
out = []
for w in W:
    x = norm(w['recipient'])
    for d in D:
        if norm(d['user']) != x: continue
        dt = ts(d['createdAt']) - ts(w['createdAt'])
        if not (0 <= dt <= 3600): continue
        a_wo, a_di = amt(w, 'out')[0], amt(d, 'in')[0]
        out.append({'sender': byp[norm(w['user'])], 'recipient': byp[norm(d['recipient'])], 'intermediary': x,
                    'withdraw_request': w['id'], 'withdraw_created': w['createdAt'], 'withdraw_in': amt(w, 'in'), 'withdraw_out': amt(w, 'out'),
                    'withdraw_inTxs': [(t.get('chainId'), t.get('hash')) for t in w['data'].get('inTxs', [])],
                    'withdraw_outTxs': [(t.get('chainId'), t.get('hash')) for t in w['data'].get('outTxs', [])],
                    'deposit_request': d['id'], 'deposit_created': d['createdAt'], 'deposit_in': amt(d, 'in'), 'deposit_out': amt(d, 'out'),
                    'deposit_inTxs': [(t.get('chainId'), t.get('hash')) for t in d['data'].get('inTxs', [])],
                    'deposit_outTxs': [(t.get('chainId'), t.get('hash')) for t in d['data'].get('outTxs', [])],
                    'seconds_between_requests': dt, 'amount_out_equals_amount_in': a_wo == a_di})
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print('requests', len(reqs), 'withdrawals', len(W), 'deposits', len(D), 'handoffs', len(out))
for h in sorted(out, key=lambda h: h['withdraw_created']):
    print(h['withdraw_created'][:19], h['sender'], '->', h['recipient'], 'via', h['intermediary'][:10], 'out', h['withdraw_out'][0], 'in', h['deposit_in'][0], 'credited', h['deposit_out'][0], 'dt', round(h['seconds_between_requests'], 1))
