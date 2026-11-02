"""Population of PROTOCOL.md section 5: every wallet with at least 500 $ of buy notional in the men's Ballon d'Or family before the ceremony. Selection on having bet, not on having won."""
import gzip
import json
from collections import defaultdict
import net

MEN = {'48361', '811116', '811117', '1105185', '1189431', '1105364', '1105369', '1105379', '1218178', '1218179', '1225367', '1225368', '1226675', '1226676'}
T_CEREMONIE = 1793044800  # 2026-10-26 20:00:00 UTC


def main():
    buy = defaultdict(float)
    first = {}
    rows = 0
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            rows += 1
            if r['eid'] in MEN and r['side'] == 'BUY' and r['ts'] < T_CEREMONIE:
                buy[r['w']] += r['size'] * r['price']
                first[r['w']] = min(first.get(r['w'], r['ts']), r['ts'])
    pop = {w: round(v, 2) for w, v in buy.items() if v >= 500}
    (net.ROOT / 'derived/population.json').write_text(json.dumps(dict(rows=rows, wallets_any_buy=len(buy), population=pop, first_buy={w: first[w] for w in pop})))
    print('rows', rows, 'wallets with any buy before ceremony', len(buy), 'population', len(pop), 'buy total', round(sum(pop.values())))


if __name__ == '__main__':
    main()
