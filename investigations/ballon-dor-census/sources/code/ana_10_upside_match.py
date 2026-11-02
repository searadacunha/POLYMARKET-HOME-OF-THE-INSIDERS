"""Does this module's own tape reproduce the 15 share counts printed in Upside's image of 23/10, and when? A name-to-wallet link for the 11 labels, tested and not inherited.
Replays net Mbappé shares per wallet on event 1105364 (both sides of each fill) and finds the time window where the printed ranking holds."""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

PRINTED = [('Thin-Disclaimer-Life', 76083), ('VidenteRibeira', 51346), ('cookedrice', 32002), ('WenZhuanBuPei', 27691), ('0x86544e4dfde', 21175), ('brace227', 17107), ('Cypyo', 15061), ('BriardxO', 14309), ('Cypya', 14170),
           ('pup1', 13946), ('mr.ozi', 12885), ('walletwallet8424', 11777), ('Zoomman17', 11158), ('enginesinmyfactory', 9462), ('kraben006', 9280)]
T_POST = 1792768669  # 23/10 15:17:49 UTC, datePublished of the first article


def main():
    rows = []
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['eid'] == '1105364' and r['oi'] == 0:
                rows.append(r)
    rows.sort(key=lambda r: r['ts'])
    outcome = rows[0]['outcome']
    print('rows on the first outcome', len(rows), 'outcome', outcome, 'wallets', len({r['w'] for r in rows}))
    pos, names = defaultdict(float), {}
    ok_windows, best = [], (-1, None)
    i = 0
    n = len(rows)
    target = [s for _, s in PRINTED]
    while i < n:
        ts = rows[i]['ts']
        while i < n and rows[i]['ts'] == ts:
            r = rows[i]
            pos[r['w']] += r['size'] if r['side'] == 'BUY' else -r['size']
            if r.get('name'):
                names.setdefault(r['w'], r['name'])
            i += 1
        if ts < T_POST - 5 * 86400 or ts > T_POST + 86400:
            continue
        top = sorted(pos.items(), key=lambda x: -x[1])[:15]
        hits = sum(abs(top[k][1] - target[k]) < 1.0 for k in range(15))
        if hits > best[0]:
            best = (hits, ts, list(top))
        if hits == 15:
            ok_windows.append(ts)
    print('best rows matched', best[0], 'of 15 at', best[1])
    if ok_windows:
        print('all 15 hold from', ok_windows[0], 'to', ok_windows[-1], 'n', len(ok_windows))
    out = []
    for k, (w, s) in enumerate(best[2]):
        printed, shares = PRINTED[k]
        known = {**seed.UPSIDE_PRINTED}.get(printed)
        out.append(dict(rank=k + 1, printed_name=printed, printed_shares=shares, wallet=w, tape_shares=round(s, 2), gap=round(s - shares, 2), tape_name=names.get(w), inventory_wallet=known, inventory_agrees=(known == w) if known else None))
        print(out[-1])
    print('later_names', {k: ([w for w, nm in names.items() if nm and nm.lower() == k.lower()], v) for k, v in seed.UPSIDE_LATER.items()})
    (net.ROOT / 'derived/upside_match.json').write_text(json.dumps(dict(best_rows=best[0], at=best[1], windows=[ok_windows[0], ok_windows[-1]] if ok_windows else None, rows=out), indent=1))


if __name__ == '__main__':
    main()
