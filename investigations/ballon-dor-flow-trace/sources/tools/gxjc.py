"""What the unidentified Solana service GxjcMTWW… does around the two sweeps of VidenteRibeira (51 489 USDT) and cookedrice (39 158 USDC): who it pays, in what, and whether any recipient receives a matching total.
An amount match here would stay a hypothesis: the service mixes many clients. Writes state/gxjc.json."""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net
import sol
import walk

GXJC = 'GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
SWEEPS = dict(vidente=dict(at=1793119916, usd=51489.0, token='USDT'), cookedrice=dict(at=1793210696, usd=39158.0, token='USDC'))
WINDOW = 6 * 3600
MAX_PAGES = 16
TX_BUDGET = 260


def signatures_back_to(oldest):
    out, before = [], None
    for _ in range(MAX_PAGES):
        opts = dict(limit=sol.PAGE)
        if before:
            opts['before'] = before
        page = sol.rpc('getSignaturesForAddress', [GXJC, opts])
        out += page
        if len(page) < sol.PAGE or (page[-1].get('blockTime') or 0) < oldest:
            break
        before = page[-1]['signature']
    return out


def main():
    sigs = signatures_back_to(min(s['at'] for s in SWEEPS.values()) - 3600)
    print('signatures', len(sigs), 'span', walk.now_utc(sigs[-1]['blockTime']), walk.now_utc(sigs[0]['blockTime']), flush=True)
    result = dict(signatures=len(sigs), span=[sigs[-1]['blockTime'], sigs[0]['blockTime']], read_at=walk.now_utc(__import__('time').time()), windows={})
    for case, sw in SWEEPS.items():
        inside = [s for s in sigs if sw['at'] <= (s.get('blockTime') or 0) <= sw['at'] + WINDOW and not s.get('err')]
        step = max(1, len(inside) // TX_BUDGET)
        sampled = inside[::step][:TX_BUDGET]
        payouts, inflows, programs, sol_payers = defaultdict(float), [], defaultdict(int), defaultdict(int)
        for s in sampled:
            tx = sol.transaction(s['signature'])
            mv = sol.moves(tx)
            for ins in tx['transaction']['message']['instructions']:
                programs[ins.get('program') or ins.get('programId')] += 1
            for m in mv:
                if m['mint'] not in sol.MINTS:
                    continue
                if m['owner'] == GXJC and m['raw'] > 0:
                    payer = next((o['owner'] for o in mv if o['mint'] == m['mint'] and o['raw'] < 0), None)
                    inflows.append(dict(payer=payer, usd=m['raw'] / 10 ** m['decimals'], token=sol.MINTS[m['mint']], at=s['blockTime']))
                elif m['owner'] != GXJC and m['raw'] > 0 and any(o['owner'] == GXJC and o['mint'] == m['mint'] and o['raw'] < 0 for o in mv):
                    payouts[(m['owner'], sol.MINTS[m['mint']])] += m['raw'] / 10 ** m['decimals']
        ranked = sorted(payouts.items(), key=lambda kv: -kv[1])[:40]
        rows = []
        for (owner, token), usd in ranked:
            lab = labels.lookup(owner, walk.SOLANA)
            rows.append(dict(owner=owner, token=token, usd=round(usd, 2), label=(lab or {}).get('name')))
        target = sw['usd'] * .99
        near = [r for r in rows if target * .9 <= r['usd'] <= sw['usd'] * 1.01]
        result['windows'][case] = dict(sweep=sw, txs_in_window=len(inside), sampled=len(sampled), sample_step=step, payout_recipients=len(payouts), payout_total=round(sum(payouts.values()), 2), inflow_count=len(inflows), inflow_total=round(sum(i['usd'] for i in inflows), 2), largest_payouts=rows[:15], recipients_near_target=near, programs=dict(sorted(programs.items(), key=lambda kv: -kv[1])[:8]))
        print(case, json.dumps({k: v for k, v in result['windows'][case].items() if k not in ('largest_payouts', 'programs')})[:600], flush=True)
        print('  top', rows[:8], flush=True)
    (net.ROOT / 'state/gxjc.json').write_text(json.dumps(result))


if __name__ == '__main__':
    main()
