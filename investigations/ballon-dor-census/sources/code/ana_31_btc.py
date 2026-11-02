"""Compte 5, Bitcoin path as published: read each address on mempool.space, a second explorer for the totals, and print every transaction as dated flows. Heuristics stay out: common inputs are written, not merged."""
import json
import sys
import time
import hist
import net
import seed

OUT = net.ROOT / 'derived/btc_denver.json'


def main():
    out = {}
    for a in seed.IRBOZ[5]['btc']:
        info = hist.btc_info(a)
        second = net.get(f'https://blockstream.info/api/address/{a}')
        txs, complete = hist.btc_txs(a)
        cs, ms = info['chain_stats'], info['mempool_stats']
        same = second['chain_stats']['funded_txo_sum'] == cs['funded_txo_sum'] and second['chain_stats']['spent_txo_sum'] == cs['spent_txo_sum']
        print(f"\n{a} funded {cs['funded_txo_sum']/1e8:.8f} spent {cs['spent_txo_sum']/1e8:.8f} txs {cs['tx_count']} complete {complete} second_explorer_agrees {same}")
        rows = []
        for t in sorted(txs, key=lambda x: (x.get('status') or {}).get('block_time') or 0):
            ts = (t.get('status') or {}).get('block_time') or 0
            ins = [(x['prevout'].get('scriptpubkey_address'), x['prevout']['value']) for x in t['vin'] if x.get('prevout')]
            outs = [(v.get('scriptpubkey_address'), v['value']) for v in t['vout']]
            mine_in = sum(v for x, v in ins if x == a)
            mine_out = sum(v for x, v in outs if x == a)
            rows.append(dict(txid=t['txid'], block=(t.get('status') or {}).get('block_height'), ts=ts, fee=t.get('fee'), n_in=len(ins), n_out=len(outs), in_this=mine_in, out_this=mine_out, inputs=ins[:12], outputs=outs[:12]))
            print(time.strftime('%Y-%m-%d %H:%M', time.gmtime(ts)), t['txid'][:12], 'in', len(ins), 'out', len(outs), f'spent_here {mine_in/1e8:.5f} got_here {mine_out/1e8:.5f}', 'to', [(str(x)[:14], round(v / 1e8, 5)) for x, v in outs if x != a][:4], 'from', sorted({str(x)[:14] for x, _ in ins if x != a})[:4])
        out[a] = dict(info=info, second_agrees=same, complete=complete, txs=rows)
    OUT.write_text(json.dumps(out))


if __name__ == '__main__':
    main()
