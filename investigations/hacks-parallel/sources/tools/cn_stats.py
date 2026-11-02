"""Outflow statistics per wallet, incident and horizon, target against control windows. Tags come from Blockscout metadata, read per batch, so a recipient with a service tag is counted apart."""
import collections
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_common as cc
import cn_windows as w
import labels
import tokens

ROOT = Path(__file__).resolve().parent.parent
HOURS = (1, 6, 24, 48)
PERSONAL_MAX_ROWS = 20  # a recipient paid more often than this inside 48 h is not read as an end user


def rounded(amount):
    return abs(amount - round(amount, -2)) < 1e-6 if amount >= 100 else abs(amount - round(amount)) < 1e-6


def stats(rows, start, hours, chain, service_tags):
    rows = [e for e in rows if start <= e['ts'] < start + hours * 3600]
    by_rcpt = collections.Counter(e['dst'] for e in rows)
    assets = collections.defaultdict(float)
    usd = 0.0
    identical = collections.Counter()
    for e in rows:
        sym = tokens.canonical_symbol(chain, e)
        q = c.amount(e)
        assets[sym] += q
        identical[(sym, e['raw'])] += 1
        if sym in cc.PRICE_KEY:
            usd += q * cc.price(sym, e['ts'])
    return dict(tx=len(rows), recipients=len(by_rcpt), service_tagged=sum(a in service_tags for a in by_rcpt), repeated_gt20=sum(n > PERSONAL_MAX_ROWS for n in by_rcpt.values()), paid_once=sum(n == 1 for n in by_rcpt.values()), usd=round(usd, 2), round_share=round(sum(rounded(c.amount(e)) for e in rows) / len(rows), 4) if rows else 0, identical_amount_tx=sum(n for n in identical.values() if n > 1), assets=json.dumps({k: round(v, 4) for k, v in sorted(assets.items(), key=lambda kv: -kv[1])[:8]}))


def main():
    out, rows_out, excluded = [], [], set()
    for incident, cfg in w.INCIDENTS.items():
        for source in cfg['sources']:
            addr, chain = w.SOURCES[source]
            target, other = cc.payouts(incident, source, 'target48')
            if target is None:
                print('missing', incident, source)
                continue
            names = cc.window_names(incident)
            everyone = {e['dst'] for n in names for e in (cc.payouts(incident, source, n)[0] or [])}
            meta = labels.metadata(everyone, chain)
            tags = {a for a in everyone if labels.is_service(labels.lookup(a, chain, meta))}
            counts = collections.Counter(e['dst'] for n in names for e in (cc.payouts(incident, source, n)[0] or []))
            excluded |= tags | {a for a, n in counts.items() if n > PERSONAL_MAX_ROWS * 3}
            for n in names:
                rows, unknown = cc.payouts(incident, source, n)
                start = cc.window_start(incident, n)
                for h in HOURS:
                    s = stats(rows, start, h, chain, tags)
                    out.append(dict(incident=incident, source=source, address=addr, chain=chain, window=n, start_utc=c.utc(start), hours=h, unknown_token_rows_48h=unknown, **s))
            for e in target:
                sym = tokens.canonical_symbol(chain, e)
                rows_out.append(dict(incident=incident, source=source, chain=chain, tx=e['tx'], block=e['block'], utc=c.utc(e['ts']), recipient=e['dst'], asset=sym, token=e['token'], decimals=e['decimals'], raw=e['raw'], amount=c.amount(e), kind=e['kind'], recipient_service_tag=e['dst'] in tags))
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/CHANGENOW_OUTBOUND_STATS.csv').open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)
    with (ROOT / 'CHANGENOW_OUTBOUND.csv').open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows_out[0]))
        wr.writeheader()
        wr.writerows(rows_out)
    (ROOT / 'state/runs/cn_excluded.json').write_text(json.dumps(sorted(excluded)))
    print(len(out), 'stat rows', len(rows_out), 'payout rows', len(excluded), 'excluded recipients')


if __name__ == '__main__':
    main()
