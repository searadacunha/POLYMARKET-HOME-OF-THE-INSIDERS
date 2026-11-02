"""Loads the frozen inputs into compact rows. Read-only on PolySentinel; aliases are not in these files."""
import gzip
import json
from pathlib import Path

S = Path.home() / 'Projects/PolySentinel/studies'
MEN = {'48361', '811116', '811117', '1189431', '1105185', '1105364', '1105369', '1105379', '1105380', '1105381', '1218178', '1218179', '1225367', '1225368', '1226675', '1226676'}
WOM = {'994444', '1105213', '1105212', '1105210', '1105391', '1105390'}
FEEDS3 = {'48361', '811116', '811117'}
T0, D1, D2, T_FIN = 1790452800, 1791849600, 1791917460, 1792768669
H = 3600
DAY = 86400


def catalog():
    """token -> (event id, market question, outcome label). Display and universes only."""
    out = {}
    for item in json.loads((S / 'ballon_2026_20261030/data/catalog_refreshed.json').read_text())['events']:
        e = item['event']
        for m in e['markets']:
            tokens, labels = m.get('clobTokenIds'), m.get('outcomes')
            tokens = json.loads(tokens) if isinstance(tokens, str) else tokens
            labels = json.loads(labels) if isinstance(labels, str) else labels
            for t, l in zip(tokens or [], labels or []):
                out[t] = (str(e['id']), m.get('question'), l)
    return out


def _lines(path):
    with gzip.open(path, 'rt') as f:
        for line in f:
            yield json.loads(line)


def family():
    """(universe, event, token, wallet, side, usd, size, price, ts, tx), M and W, T0 <= ts < T_FIN, each row once."""
    seen = 0
    for r in _lines(S / 'ballon_2026_20261030/data/trades_minimal.jsonl.gz'):
        e = str(r['event_id'])
        if e in FEEDS3 or not T0 <= r['timestamp'] < T_FIN:
            continue
        u = 'M' if e in MEN else 'W' if e in WOM else None
        if u:
            seen += 1
            yield (u, e, r['token_id'], r['wallet'], r['side'], r['size'] * r['price'], r['size'], r['price'], r['timestamp'], r['transaction_hash'])
    for r in _lines(S / 'pipeline_replay_20261101/data/family_extra.jsonl.gz'):
        if T0 <= r['timestamp'] < T_FIN:
            yield ('M', r['source_event'], r['token_id'], r['proxy_wallet'], r['side'], r['size'] * r['price'], r['size'], r['price'], r['timestamp'], r['transaction_hash'])


def controls():
    sample = json.loads((S / 'pipeline_replay_20261101/data/sample.json').read_text())
    strata = {u['slug']: u['strate'] for u in sample['unites'] if u['statut'] == 'inclus'}
    for r in _lines(S / 'pipeline_replay_20261101/data/controls.jsonl.gz'):
        event = r['source_event']
        if event in strata and T0 <= r['timestamp'] < T_FIN:
            yield ('X:' + strata[event], event, r['token_id'], r['proxy_wallet'], r['side'], r['size'] * r['price'], r['size'], r['price'], r['timestamp'], r['transaction_hash'])


def census(family_tokens):
    """Census rows, tagged G, or M/W when the token belongs to those families."""
    for r in _lines(S / 'pipeline_replay_20261101/data/global_window.jsonl.gz'):
        if r['timestamp'] < T_FIN:
            yield (family_tokens.get(r['token_id'], 'G'), r.get('event_slug'), r['token_id'], r['proxy_wallet'], r['side'], r['size'] * r['price'], r['size'], r['price'], r['timestamp'], r['transaction_hash'])
